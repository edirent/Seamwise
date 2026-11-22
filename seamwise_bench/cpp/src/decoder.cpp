#include "seamwise/decoder.hpp"
#include "bp.hpp"
#include "lsd.hpp"
#include "osd.hpp"
#include <cassert>
#include <cmath>
#include <iterator>
#include <stdexcept>
#include <tuple>
#include <climits>

namespace seamwise {
// Faithful scalar port of the MIT-licensed ldpc 2.4.1 parallel normalized
// min-sum path (vendor/ldpc/LICENSE). Prefix/suffix order and <=0 signs match
// bp.hpp exactly; only immutable prior preparation and message storage change.
struct FlatBP {
    const Matrix&model;
    std::vector<double>prior,llr,bit_to_check,check_to_bit;
    Bytes decoding,candidate;
    int maximum_iterations,iterations=0;
    bool converge=false;
    FlatBP(const Matrix&m,int it):model(m),maximum_iterations(it){
        prior.resize(m.m);llr.resize(m.m);bit_to_check.resize(m.edges.size());check_to_bit.resize(m.edges.size());decoding.resize(m.m);candidate.resize(m.n);
        for(int j=0;j<m.m;++j)prior[j]=std::log((1-m.probabilities[j])/m.probabilities[j]);
    }
    Bytes decode(const Bytes&s){
        converge=false;
        for(int j=0;j<model.m;++j)for(int e:model.inc[model.n+j])bit_to_check[e]=prior[j];
        for(int it=1;it<=maximum_iterations;++it){
            for(int i=0;i<model.n;++i){
                candidate[i]=0;int total_sign=s[i];double temp=std::numeric_limits<double>::max();
                for(int e:model.inc[i]){if(bit_to_check[e]<=0)++total_sign;check_to_bit[e]=temp;double ab=std::abs(bit_to_check[e]);if(ab<temp)temp=ab;}
                temp=std::numeric_limits<double>::max();
                for(auto p=model.inc[i].rbegin();p!=model.inc[i].rend();++p){int e=*p;int sign=total_sign;if(bit_to_check[e]<=0)++sign;if(temp<check_to_bit[e])check_to_bit[e]=temp;int message_sign=(sign%2==0)?1:-1;check_to_bit[e]*=message_sign*.625;double ab=std::abs(bit_to_check[e]);if(ab<temp)temp=ab;}
            }
            for(int j=0;j<model.m;++j){double temp=prior[j];for(int e:model.inc[model.n+j]){bit_to_check[e]=temp;temp+=check_to_bit[e];}llr[j]=temp;decoding[j]=temp<=0;
                if(decoding[j])for(int e:model.inc[model.n+j])candidate[model.edges[e].first]^=1;
            }
            converge=candidate==s;iterations=it;if(converge)return decoding;
            for(int j=0;j<model.m;++j){double temp=0;for(auto p=model.inc[model.n+j].rbegin();p!=model.inc[model.n+j].rend();++p){int e=*p;bit_to_check[e]+=temp;temp+=check_to_bit[e];}}
        }
        return decoding;
    }
};
struct NativeBackend {
    std::unique_ptr<ldpc::bp::BpSparse> pcm;
    std::unique_ptr<ldpc::bp::BpDecoder> bp;
    std::unique_ptr<ldpc::lsd::LsdDecoder> lsd;
    std::unique_ptr<ldpc::osd::OsdDecoder> osd;
    std::unique_ptr<FlatBP> flat;
};
LocalSolver::~LocalSolver()=default;
using Clock=std::chrono::steady_clock;
static uint64_t ns(Clock::time_point t) { return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-t).count(); }
Support sx(const Support&a,const Support&b) {
    Support r; r.reserve(a.size()+b.size());
    std::set_symmetric_difference(a.begin(),a.end(),b.begin(),b.end(),std::back_inserter(r));return r;
}
static Support su(const Support&a,const Support&b) {
    Support r;r.reserve(a.size()+b.size());
    std::set_union(a.begin(),a.end(),b.begin(),b.end(),std::back_inserter(r));return r;
}
void Basis::insert(const Support&column,int j,Counters*c) {
    Support v=column,w={j};
    if(c) ++c->insertions;
#ifdef SEAMWISE_INDEXED_REDUCTION
    // An XOR at pivot p creates bits only BELOW p. Visiting the next present
    // bit below the cursor is therefore equivalent to scanning every pivot in
    // descending order, while skipping pivots absent from the current column.
    int cursor=INT_MAX;
    while(true) {
        auto bit=std::lower_bound(v.begin(),v.end(),cursor);
        if(bit==v.begin())break;
        int p=*std::prev(bit);cursor=p;auto pivot=pivots.find(p);
        if(pivot==pivots.end())continue;
        const auto&e=pivot->second;
#else
    for(const auto&[p,e]:pivots) if(std::binary_search(v.begin(),v.end(),p)) {
#endif
        if(c) c->xor_entries+=v.size()+e.column.size()+w.size()+e.witness.size();
        v=sx(v,e.column);w=sx(w,e.witness);
    }
    inserted.insert(std::lower_bound(inserted.begin(),inserted.end(),j),j);
    if(v.empty()){if(c)++c->dependent_columns;return;} // deterministic dependent free variable=0
    int p=v.back();
    if(std::binary_search(residual.begin(),residual.end(),p)) { if(c)c->xor_entries+=residual.size()+v.size()+witness.size()+w.size();residual=sx(residual,v);witness=sx(witness,w); }
    pivots.emplace(p,Entry{std::move(v),std::move(w)});
}
void Basis::merge(Basis&&b,Counters*c) {
    if(c)c->xor_entries+=residual.size()+b.residual.size()+witness.size()+b.witness.size();
    residual=sx(residual,b.residual);witness=sx(witness,b.witness);inserted=su(inserted,b.inserted);
    if(c) for(const auto&[p,e]:b.pivots)c->witness_bytes+=e.witness.size()*sizeof(int);
    pivots.merge(b.pivots);
    if(!b.pivots.empty())throw std::logic_error("merge pivot supports overlap");
}
Matrix::Matrix(int rows,std::vector<Support> cols,std::vector<double>p,std::vector<double>w):n(rows),m(cols.size()),columns(std::move(cols)),probabilities(std::move(p)),weights(std::move(w)) {
    if(n<0||probabilities.size()!=columns.size()||weights.size()!=columns.size())throw std::invalid_argument("matrix dimensions");
    inc.resize(n+m);
    for(int j=0;j<m;++j) {
        if(!(probabilities[j]>0 && probabilities[j]<1)||!std::isfinite(weights[j]))throw std::invalid_argument("finite priors in (0,1) required");
        const auto&v=columns[j];
        if(!std::is_sorted(v.begin(),v.end())||std::adjacent_find(v.begin(),v.end())!=v.end())throw std::invalid_argument("sorted unique supports required");
        for(int i:v) {
            if(i<0||i>=n)throw std::invalid_argument("detector index out of range");
            int e=edges.size();edges.emplace_back(i,n+j);inc[i].push_back(e);inc[n+j].push_back(e);
        }
    }
}
Bytes Matrix::apply(const Bytes&x)const {
    if(x.size()!=size_t(m))throw std::invalid_argument("correction length");
    Bytes s(n,0);for(int j=0;j<m;++j)if(x[j])for(int i:columns[j])s[i]^=1;return s;
}
uint64_t Matrix::storage_bytes()const {
    uint64_t out=sizeof(*this)+edges.capacity()*sizeof(edges[0])+(probabilities.capacity()+weights.capacity())*sizeof(double);
    for(const auto&v:columns)out+=sizeof(v)+v.capacity()*sizeof(int);
    for(const auto&v:inc)out+=sizeof(v)+v.capacity()*sizeof(int);return out;
}
LocalSolver::LocalSolver(Matrix a,std::string f,bool persist,bool diagnostics,int it,int ord,bool dense):model(std::move(a)),family(std::move(f)),persistent(persist),audit(diagnostics),dense_terminal(dense) {
    native=std::make_unique<NativeBackend>();
    auto&pcm=native->pcm;auto&bp=native->bp;auto&lsd=native->lsd;auto&osd=native->osd;
    bp_enabled=family=="bphuf"||family=="lsd"||family=="osd";
    if(family!="huf"&&!bp_enabled)throw std::invalid_argument("unknown native solver family");
    int v=model.n+model.m;
    parent.resize(v);size.resize(v);label.resize(v);head.resize(v);tail.resize(v);next.resize(v);
    missing.resize(model.m);states.resize(v);frontier.resize(v);materialized.resize(v);clocks.resize(model.edges.size());priority=model.weights;
    if(bp_enabled && model.n && model.m) {
#ifdef SEAMWISE_FLAT_BP
        if(family=="bphuf"){native->flat=std::make_unique<FlatBP>(model,it);return;}
#endif
        pcm=std::make_unique<ldpc::bp::BpSparse>(model.n,model.m,model.edges.size());
        // Python's CSC conversion inserts in column-major order too.
        for(int j=0;j<model.m;++j)for(int i:model.columns[j])pcm->insert_entry(i,j);
        bp=std::make_unique<ldpc::bp::BpDecoder>(*pcm,model.probabilities,it,ldpc::bp::MINIMUM_SUM,ldpc::bp::PARALLEL,.625,1,ldpc::bp::NULL_INT_VECTOR,0,false,ldpc::bp::SYNDROME);
        if(family=="lsd")lsd=std::make_unique<ldpc::lsd::LsdDecoder>(*pcm,ord?ldpc::osd::COMBINATION_SWEEP:ldpc::osd::OSD_0,ord);
        if(family=="osd")osd=std::make_unique<ldpc::osd::OsdDecoder>(*pcm,ord?ldpc::osd::COMBINATION_SWEEP:ldpc::osd::OSD_0,ord,bp->channel_probabilities);
    }
}
int LocalSolver::root(int u) {
    if(audit)++counts.roots;
    while(parent[u]!=u){parent[u]=parent[parent[u]];u=parent[u];}return u;
}
Basis&LocalSolver::state(int r,const Bytes&s) {
    if(!states[r]) {
        Support t;if(size[r]!=1)throw std::logic_error("unmaterialized composite state");
        if(r<model.n&&s[r])t.push_back(r);
        states[r]=std::make_unique<Basis>(std::move(t));if(audit)++counts.state_initializations;
    }return *states[r];
}
const Support&LocalSolver::boundary(int r) {
    if(!materialized[r]){frontier[r]=model.inc[r];materialized[r]=1;}return frontier[r];
}
Basis LocalSolver::fresh(const Support&faults,const Support&target) {
    Basis s(target);Support ordered=faults;
    if(bp_enabled)std::sort(ordered.begin(),ordered.end(),[&](int a,int b){return std::tie(priority[a],a)<std::tie(priority[b],b);});
    for(int j:ordered)s.insert(model.columns[j],j,audit?&counts:nullptr);return s;
}
Support LocalSolver::canonical(const Support&faults,const Support&target) {
    if(!dense_terminal)return fresh(faults,target).witness;
    // Cluster-local coordinates, packed scalar uint64_t rows and provenance.
    // This is an exact terminal implementation ablation, never a new policy.
    Support rows;for(int j:faults)rows=su(rows,model.columns[j]);
    for(int i:target)if(!std::binary_search(rows.begin(),rows.end(),i))throw std::runtime_error("invalid terminal");
    Support ordered=faults;
    if(bp_enabled)std::sort(ordered.begin(),ordered.end(),[&](int a,int b){return std::tie(priority[a],a)<std::tie(priority[b],b);});
    size_t rw=(rows.size()+63)/64,cw=(faults.size()+63)/64;
    std::vector<std::vector<uint64_t>> vs(rows.size()),ws(rows.size());
    std::vector<uint64_t> residual(rw),out(cw);
    for(int i:target){int k=std::lower_bound(rows.begin(),rows.end(),i)-rows.begin();residual[k/64]^=uint64_t(1)<<(k%64);}
    for(int j:ordered){
        std::vector<uint64_t>v(rw),w(cw);int fj=std::lower_bound(faults.begin(),faults.end(),j)-faults.begin();w[fj/64]^=uint64_t(1)<<(fj%64);
        for(int i:model.columns[j]){int k=std::lower_bound(rows.begin(),rows.end(),i)-rows.begin();v[k/64]^=uint64_t(1)<<(k%64);}
        // Match State.insert: reduce against EVERY existing pivot before
        // selecting a new pivot, including pivots below a missing high bit.
        for(int k=int(rows.size())-1;k>=0;--k)if(!vs[k].empty()&&((v[k/64]>>(k%64))&1)) {
            for(size_t q=0;q<rw;++q)v[q]^=vs[k][q];for(size_t q=0;q<cw;++q)w[q]^=ws[k][q];if(audit)counts.xor_words+=rw+cw;
        }
        for(int k=int(rows.size())-1;k>=0;--k)if((v[k/64]>>(k%64))&1){vs[k]=v;ws[k]=w;if((residual[k/64]>>(k%64))&1){for(size_t q=0;q<rw;++q)residual[q]^=v[q];for(size_t q=0;q<cw;++q)out[q]^=w[q];if(audit)counts.xor_words+=rw+cw;}break;}
    }
    if(std::any_of(residual.begin(),residual.end(),[](uint64_t v){return v!=0;}))throw std::runtime_error("invalid terminal");
    Support w;for(size_t j=0;j<faults.size();++j)if((out[j/64]>>(j%64))&1)w.push_back(faults[j]);return w;
}
Bytes LocalSolver::grow(const Bytes&s) {
    const int n=model.n,m=model.m,v=n+m;History hist;
    Support diagnostic_checks,diagnostic_incidences;
    if(audit){diagnostic_checks.assign(v,0);std::fill_n(diagnostic_checks.begin(),n,1);diagnostic_incidences.assign(v,0);}
    std::iota(parent.begin(),parent.end(),0);std::iota(label.begin(),label.end(),0);std::iota(head.begin(),head.end(),0);std::iota(tail.begin(),tail.end(),0);
    std::fill(size.begin(),size.end(),1);std::fill(next.begin(),next.end(),-1);std::fill(materialized.begin(),materialized.end(),0);
    for(auto&st:states)st.reset();for(auto&f:frontier)f.clear();
    for(int j=0;j<m;++j)missing[j]=model.columns[j].size();
    for(size_t e=0;e<clocks.size();++e)clocks[e]=std::max(1e-9,priority[model.edges[e].second-n]);
    using Item=std::pair<int,int>;
    std::priority_queue<Item,std::vector<Item>,std::greater<Item>>heap;
    for(int i=0;i<n;++i)if(s[i])heap.emplace(1,i);
    auto target_for=[&](int r){Support t;for(int u=head[r];u>=0;u=next[u])if(u<n&&s[u])t.push_back(u);std::sort(t.begin(),t.end());return t;};
    auto t0=Clock::now();
    while(!heap.empty()) {
        auto [sz,canonical_label]=heap.top();heap.pop();int r=root(canonical_label);
        if(label[r]!=canonical_label||size[r]!=sz||state(r,s).residual.empty()){if(audit)++counts.stale_heap;continue;}
        const auto&bd=boundary(r);
        if(bd.empty()){if(audit){counts.growth_ns+=ns(t0);histories.push_back(hist);}return Bytes(m,0);}
        double delta=std::numeric_limits<double>::infinity();
        for(int e:bd)delta=std::min(delta,clocks[e]);
        Support sat;for(int e:bd){clocks[e]-=delta;if(clocks[e]<=1e-8)sat.push_back(e);}
        if(audit)counts.frontier_visits+=2*bd.size();
        for(int e:sat) {
            auto [u,w]=model.edges[e];int a=root(u),b=root(w);if(a==b)continue;
            int ca=label[a],cb=label[b];if(ca>cb)std::swap(ca,cb);
            // Internal identity uses size; public identity always minimum vertex.
            if(size[a]<size[b])std::swap(a,b);
            Support newly;
            int internalized=0;
            // INVARIANT missing[j] equals the number of incidence edges whose
            // detector and fault vertices have different roots. Only edges
            // crossing these two components become internal at this union.
            for(int moved=head[b];moved>=0;moved=next[moved])for(int f:model.inc[moved]) {
                if(audit)++counts.eligibility_visits;
                auto [i,fault]=model.edges[f];int other=moved==i?fault:i;
                if(root(other)==a){if(audit)++internalized;int j=fault-n;if(--missing[j]==0)newly.push_back(j);}
            }
            auto merged_frontier=sx(boundary(a),boundary(b));
            auto&sa=state(a,s);auto&sb=state(b,s);
            if(persistent)sa.merge(std::move(sb),audit?&counts:nullptr);
            else sa.inserted=su(sa.inserted,sb.inserted);
            // A rebuilding oracle reconstructs once after the growth event.
            // Discarded pivot/witness merges are not intrinsic rebuilding work.
            states[b].reset();
            parent[b]=a;size[a]+=size[b];label[a]=std::min(label[a],label[b]);
            next[tail[a]]=head[b];tail[a]=tail[b];
            frontier[a]=std::move(merged_frontier);frontier[b].clear();materialized[a]=1;
            if(audit){diagnostic_checks[a]+=diagnostic_checks[b];diagnostic_incidences[a]+=diagnostic_incidences[b]+internalized;hist.merge_detectors.push_back(diagnostic_checks[a]);hist.merge_faults.push_back(size[a]-diagnostic_checks[a]);hist.merge_incidences.push_back(diagnostic_incidences[a]);}
            std::sort(newly.begin(),newly.end());
            for(int j:newly) {
                if(persistent)sa.insert(model.columns[j],j,audit?&counts:nullptr);
                else sa.inserted.insert(std::lower_bound(sa.inserted.begin(),sa.inserted.end(),j),j);
            }
            if(audit){++counts.merges;counts.activations+=newly.size();counts.frontier_updates+=frontier[a].size();hist.merge_sizes.push_back(size[a]);Support event={ca,cb,label[a],size[a]};event.insert(event.end(),newly.begin(),newly.end());hist.semantic_merges.push_back(std::move(event));}
            r=a;
        }
        r=root(r);
        if(!persistent){auto st=fresh(states[r]->inserted,target_for(r));*states[r]=std::move(st);}
        if(!states[r]->residual.empty())heap.emplace(size[r],label[r]);
    }
    if(audit)counts.growth_ns+=ns(t0);t0=Clock::now();
    Bytes out(m,0);
    // Ascending public labels preserve reference dictionary terminal order.
    for(int i=0;i<v;++i)if(parent[i]==i&&states[i]&&!states[i]->inserted.empty()){
        if(audit)hist.final_ranks.push_back(states[i]->pivots.size());
        auto t=target_for(i);Support w;
        if(dense_terminal)w=canonical(states[i]->inserted,t);
        else {auto terminal=fresh(states[i]->inserted,t);if(!terminal.residual.empty())throw std::runtime_error("invalid terminal");w=std::move(terminal.witness);}
        for(int j:w)out[j]^=1;
    }
    if(model.apply(out)!=s)throw std::runtime_error("invalid global correction"); // intrinsic reference decision
    if(audit){counts.terminal_ns+=ns(t0);hist.success=true;histories.push_back(std::move(hist));}
    return out;
}
Bytes LocalSolver::decode(const Bytes&syn) {
    auto&bp=native->bp;auto&lsd=native->lsd;auto&osd=native->osd;
    if(syn.size()!=size_t(model.n)||std::any_of(syn.begin(),syn.end(),[](uint8_t b){return b>1;}))throw std::invalid_argument("binary syndrome length");
    if(!bp&&!native->flat){priority=model.weights;return grow(syn);}
    // The official Python BpDecoder binding bypasses BP on zero input,
    // leaves its previous LLR diagnostics untouched, and declares convergence.
    if(std::none_of(syn.begin(),syn.end(),[](uint8_t v){return v!=0;})) {
        if(bp)bp->converge=true;
        if(native->flat)native->flat->converge=true;
        if(audit){++counts.bp_converged;History h;h.success=true;h.bp_converged=true;histories.push_back(h);}
        return Bytes(model.m,0);
    }
    Bytes s=syn;auto t0=Clock::now();Bytes x;std::vector<double>*llrs;bool converged;int iterations;
    if(native->flat){auto&f=*native->flat;x=f.decode(s);llrs=&f.llr;converged=f.converge;iterations=f.iterations;}
    else{x=bp->decode(s);llrs=&bp->log_prob_ratios;converged=bp->converge;iterations=bp->iterations;}
    if(audit)last_llr=*llrs;
    if(audit){counts.bp_ns+=ns(t0);counts.bp_iterations+=iterations;counts.bp_converged+=converged;}
    if(converged){if(audit){History h;h.success=true;h.bp_converged=true;histories.push_back(h);}return x;}
    if(lsd)return lsd->lsd_decode(s,bp->log_prob_ratios,1,true);
    if(osd)return osd->decode(s,bp->log_prob_ratios);
    Bytes base(model.m);
    for(int j=0;j<model.m;++j){double llr=std::clamp((*llrs)[j],-100.,100.);base[j]=llr<0;priority[j]=std::abs(llr);}
    auto removed=model.apply(base);for(int i=0;i<model.n;++i)s[i]^=removed[i];
    auto y=grow(s);for(int j=0;j<model.m;++j)y[j]^=base[j];return y;
}
uint64_t LocalSolver::workspace_bytes()const {
    uint64_t b=(parent.capacity()+size.capacity()+label.capacity()+head.capacity()+tail.capacity()+next.capacity()+missing.capacity())*sizeof(int)+(clocks.capacity()+priority.capacity())*sizeof(double)+states.capacity()*sizeof(states[0])+materialized.capacity();
    for(const auto&v:frontier)b+=sizeof(v)+v.capacity()*sizeof(int);
    for(const auto&s:states)if(s){b+=sizeof(Basis)+(s->residual.capacity()+s->witness.capacity()+s->inserted.capacity())*sizeof(int);for(const auto&[p,e]:s->pivots)b+=sizeof(e)+sizeof(int)+3*sizeof(void*)+(e.column.capacity()+e.witness.capacity())*sizeof(int);}
    if(native->flat){const auto&f=*native->flat;b+=(f.prior.capacity()+f.llr.capacity()+f.bit_to_check.capacity()+f.check_to_bit.capacity())*sizeof(double)+f.decoding.capacity()+f.candidate.capacity();}
    if(native->bp){const auto&f=*native->bp;b+=(f.channel_probabilities.capacity()+f.log_prob_ratios.capacity()+f.initial_log_prob_ratios.capacity()+f.soft_syndrome.capacity())*sizeof(double)+f.decoding.capacity()+f.candidate_syndrome.capacity()+f.serial_schedule_order.capacity()*sizeof(int);}
    return b; // owned vector capacities + estimated map payload; excludes allocator overhead and LDPC internals
}
Decoder::Decoder(int n,std::vector<Support>d,std::vector<Support>l,std::vector<double>p,std::vector<double>w,Support lab,int b,std::string f,bool persist,std::string pol,bool diagnostics,int it,int ord,bool dense):model(n,std::move(d),std::move(p),std::move(w)),logical(std::move(l)),labels(std::move(lab)),blocks(b),family(std::move(f)),policy(std::move(pol)),persistent(persist),audit(diagnostics),dense_terminal(dense),iterations(it),order(ord) {
    if(labels.size()!=size_t(n)||blocks<1||logical.size()!=size_t(model.m))throw std::invalid_argument("partition dimensions");
    for(const auto&v:logical)for(int i:v){if(i<0)throw std::invalid_argument("negative observable index");observable_count=std::max(observable_count,i+1);}
    for(int v:labels)if(v<0||v>=blocks)throw std::invalid_argument("partition label range");
    if(policy!="joint"&&policy!="cut"&&policy!="halo1"&&policy!="halo2"&&policy!="repair1"&&policy!="repair2")throw std::invalid_argument("unsupported policy");
    owner.assign(model.m,blocks);
    for(int j=0;j<model.m;++j){for(int i:model.columns[j])owner[j]=std::min(owner[j],labels[i]);if(owner[j]==blocks)zero.push_back(j);}
    global=std::make_unique<LocalSolver>(model,family,persistent,audit,iterations,order,dense_terminal);
    if(policy=="joint")return;
    int halo=policy.rfind("halo",0)==0?policy.back()-'0':0;
    for(int start=0;start<blocks;start+=core){
        int end=std::min(blocks,start+core+halo);Support cols,rows,external(n),touched(n),cr;
        for(int j=0;j<model.m;++j){if(owner[j]>=start&&owner[j]<end){cols.push_back(j);for(int i:model.columns[j])touched[i]=1;}if(owner[j]>=end&&owner[j]<blocks)for(int i:model.columns[j])++external[i];}
        for(int i=0;i<n;++i){bool iscore=labels[i]>=start&&labels[i]<std::min(blocks,start+core);if((touched[i]&&!external[i])||iscore)rows.push_back(i);if(iscore)cr.push_back(i);}
        auto win=window(std::move(cols),std::move(rows));win.core_rows=std::move(cr);
        for(int j:win.columns)win.commit.push_back(owner[j]<std::min(blocks,start+core));cutplans.push_back(std::move(win));
    }
    if(policy.rfind("repair",0)==0){int radius=policy.back()-'0';for(int seam=core;seam<blocks;seam+=core){Support cols,rows,touched(n);for(int j=0;j<model.m;++j)if(owner[j]>=std::max(0,seam-radius)&&owner[j]<std::min(blocks,seam+radius)){cols.push_back(j);for(int i:model.columns[j])touched[i]=1;}for(int i=0;i<n;++i)if(touched[i])rows.push_back(i);bands.push_back(window(std::move(cols),std::move(rows)));}}
}
Window Decoder::window(Support cols,Support rows){
    Window win;win.columns=std::move(cols);win.rows=std::move(rows);
    std::vector<Support>local;std::vector<double>p,w;Support map(model.n,-1);for(size_t i=0;i<win.rows.size();++i)map[win.rows[i]]=i;
    for(int j:win.columns){Support v;for(int i:model.columns[j])if(map[i]>=0)v.push_back(map[i]);local.push_back(std::move(v));p.push_back(model.probabilities[j]);w.push_back(model.weights[j]);}
    if(!win.columns.empty())win.solver=std::make_unique<LocalSolver>(Matrix(win.rows.size(),std::move(local),std::move(p),std::move(w)),family,persistent,audit,iterations,order,dense_terminal);return win;
}
Bytes Decoder::joint(const Bytes&s){auto x=global->decode(s);for(int j:zero)x[j]=model.probabilities[j]>.5;return x;}
Bytes Decoder::cut(const Bytes&s,bool&fallback){
    Bytes x(model.m,0),res=s;for(int j:zero)x[j]=model.probabilities[j]>.5;
    for(auto&win:cutplans){
        if(!win.solver){for(int i:win.core_rows)if(res[i]){fallback=true;return joint(s);}continue;}
        Bytes target;for(int i:win.rows)target.push_back(res[i]);auto z=win.solver->decode(target);
        if(win.solver->model.apply(z)!=target){fallback=true;return joint(s);}
        for(size_t k=0;k<win.columns.size();++k)if(win.commit[k]){int j=win.columns[k];x[j]=z[k];if(z[k])for(int i:model.columns[j])res[i]^=1;}
        for(int i:win.core_rows)if(res[i]){fallback=true;return joint(s);}
    }
    if(std::any_of(res.begin(),res.end(),[](uint8_t v){return v!=0;})){fallback=true;return joint(s);}return x;
}
Bytes Decoder::frame(const Bytes&x)const {Bytes y(observable_count,0);for(int j=0;j<model.m;++j)if(x[j])for(int i:logical[j]){if(i>=observable_count)throw std::logic_error("observable count truncation");y[i]^=1;}return y;}
Result Decoder::decode(const Bytes&s){
    if(s.size()!=size_t(model.n))throw std::invalid_argument("syndrome length");Result out;auto t=Clock::now();
    out.correction=policy=="joint"?joint(s):cut(s,out.fallback);
    if(audit){counts.cut_ns+=ns(t);counts.fallback+=out.fallback;}t=Clock::now();
    if(!bands.empty()&&model.apply(out.correction)==s){int seam=core;for(auto&win:bands){
        RepairEvent e;e.seam=seam;seam+=core;if(!win.solver)continue;
        Bytes old;for(int j:win.columns){old.push_back(out.correction[j]);e.oldcost+=model.weights[j]*out.correction[j];}
        auto target=win.solver->model.apply(old);auto z=win.solver->decode(target);e.consistent=win.solver->model.apply(z)==target;
        for(size_t k=0;k<win.columns.size();++k)e.newcost+=model.weights[win.columns[k]]*z[k];
        if(e.consistent&&e.newcost<e.oldcost-1e-10){e.accepted=true;for(size_t k=0;k<win.columns.size();++k)out.correction[win.columns[k]]=z[k];}
        if(audit){++counts.repair_calls;counts.accepted+=e.accepted;out.events.push_back(e);}
    }}
    if(audit)counts.repair_ns+=ns(t);t=Clock::now();out.frame=frame(out.correction);if(audit)counts.frame_ns+=ns(t);return out;
}
std::vector<LocalSolver*>Decoder::solvers(){std::vector<LocalSolver*>out={global.get()};for(auto&w:cutplans)if(w.solver)out.push_back(w.solver.get());for(auto&w:bands)if(w.solver)out.push_back(w.solver.get());return out;}
uint64_t Decoder::prepared_bytes()const{uint64_t b=model.storage_bytes();for(const auto&w:cutplans){b+=(w.columns.capacity()+w.rows.capacity()+w.core_rows.capacity())*sizeof(int)+w.commit.capacity();if(w.solver)b+=w.solver->model.storage_bytes();}for(const auto&w:bands){b+=(w.columns.capacity()+w.rows.capacity())*sizeof(int);if(w.solver)b+=w.solver->model.storage_bytes();}if(global)b+=global->model.storage_bytes();for(const auto&v:logical)b+=sizeof(v)+v.capacity()*sizeof(int);return b;}
}
