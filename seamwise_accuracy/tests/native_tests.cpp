#include "seamwise/decoder.hpp"
#include "seamwise/policy.hpp"
#include <iostream>
#include <random>
#include <cmath>
#include <stdexcept>
using namespace seamwise;
static void require(bool b){if(!b)throw std::runtime_error("test invariant failed");}
static Support support(unsigned x){Support v;for(int i=0;x;++i,x>>=1)if(x&1)v.push_back(i);return v;}
static unsigned mask(const Support&s){unsigned x=0;for(int i:s)x^=1u<<i;return x;}
int main(){
    uint64_t cases=0;
    // Includes zero columns, repeated supports, inconsistent and zero targets.
    for(unsigned code=0;code<64;++code){std::vector<Support>cs={support(code&3),support((code>>2)&3),support((code>>4)&3)};
      for(unsigned t=0;t<4;++t){Basis s(support(t));for(int j=0;j<3;++j)s.insert(cs[j],j);
        bool possible=false;for(unsigned x=0;x<8;++x){unsigned z=0;for(int j=0;j<3;++j)if((x>>j)&1)z^=mask(cs[j]);possible|=z==t;}
        require(s.residual.empty()==possible);unsigned z=0;for(int j:s.witness)z^=mask(cs[j]);require((z^mask(s.residual))==t);++cases;
      }
      // Native witnesses generate every dependent-column relation. Their
      // logical image rank must equal rank([D;L])-rank(D), for every L.
      Basis detector;for(int j=0;j<3;++j)detector.insert(cs[j],j);
      std::vector<Support> relations;
      for(int j=0;j<3;++j){Basis prior(cs[j]);for(int k=0;k<j;++k)prior.insert(cs[k],k);if(prior.residual.empty())relations.push_back(sx(prior.witness,Support{j}));}
      require(relations.size()==3-detector.pivots.size());
      for(unsigned logical=0;logical<8;++logical){Basis stacked,images;for(int j=0;j<3;++j){auto col=cs[j];if((logical>>j)&1)col.push_back(2);stacked.insert(col,j);}
        for(size_t k=0;k<relations.size();++k){unsigned image=0;for(int j:relations[k])image^=(logical>>j)&1;images.insert(support(image),k);}
        require(images.pivots.size()==stacked.pivots.size()-detector.pivots.size());++cases;
      }
    }
    std::mt19937 rng(20261109);
    for(int k=0;k<1200;++k){int n=1+rng()%9,m=1+rng()%14;std::vector<Support>cs;for(int j=0;j<m;++j)cs.push_back(support(rng()&((1u<<n)-1)));std::vector<double>p(m,.03),w(m,1.);Matrix a(n,cs,p,w);
      Bytes x(m);for(auto&b:x)b=rng()&1;auto syn=a.apply(x);
      LocalSolver r(a,"huf",false,true),s(a,"huf",true,true),d(a,"huf",true,true,30,0,true);
      Bytes rx,sx_,dx;
      try{rx=r.decode(syn);sx_=s.decode(syn);dx=d.decode(syn);}catch(const std::exception&e){std::cerr<<"trial="<<k<<" n="<<n<<" m="<<m<<" columns=";for(auto&v:cs)std::cerr<<mask(v)<<',';std::cerr<<" syndrome=";for(auto b:syn)std::cerr<<int(b);std::cerr<<' '<<e.what()<<'\n';throw;}
      require(rx==sx_&&rx==dx&&a.apply(rx)==syn);
      require(r.histories.back().semantic_merges==s.histories.back().semantic_merges);
      if(k<100){
        LocalSolver flat(a,"bphuf",true,true),official(a,"lsd",false,true);
        flat.decode(syn);official.decode(syn);
        require(flat.last_llr.size()==official.last_llr.size());
        for(size_t j=0;j<flat.last_llr.size();++j)require(flat.last_llr[j]==official.last_llr[j] || (std::isnan(flat.last_llr[j])&&std::isnan(official.last_llr[j])));
        require(flat.counts.bp_iterations==official.counts.bp_iterations);
        LocalSolver damped(a,"bphuf",true,true),serial(a,"bphuf",true,true);
        configure_bp(damped,.8,.25,false);configure_bp(serial,.8,0,true);
        auto damped_x=damped.decode(syn),serial_x=serial.decode(syn);
        require(a.apply(damped_x)==syn&&a.apply(serial_x)==syn);
        damped.decode(Bytes(n,0));serial.decode(Bytes(n,0));
        require(damped.decode(syn)==damped_x&&serial.decode(syn)==serial_x);
      }
      // Capacity reuse/reset and repeated syndrome order independence.
      Bytes zero(n,0);s.decode(zero);require(s.decode(syn)==sx_);++cases;
    }
    for(int trial=0;trial<100;++trial){
      int n=rng()%5,m=1+rng()%6;std::vector<Support>cs,ls;
      for(int j=0;j<m;++j){cs.push_back(support(rng()&((1u<<n)-1)));ls.push_back(support(rng()%4));}
      std::vector<double>p(m,.1),w(m);for(auto&v:w)v=1+rng()%3;Support labels(n);for(auto&v:labels)v=rng()%4;
      Matrix model(n,cs,p,w);Bytes sampled(m);for(auto&v:sampled)v=rng()%2;auto syndrome=model.apply(sampled);
      std::map<int,std::vector<std::vector<Support>>>moves;
      for(int radius:{1,2}){Decoder geometry(n,cs,ls,p,w,labels,4,"huf",true,"repair"+std::to_string(radius));
        for(auto&win:geometry.bands){std::vector<Support>local;
          if(win.solver)for(unsigned v=1;v<(1u<<win.columns.size());++v){Bytes x(win.columns.size());for(size_t j=0;j<x.size();++j)x[j]=(v>>j)&1;auto parity=win.solver->model.apply(x);if(std::none_of(parity.begin(),parity.end(),[](auto b){return b;}))local.push_back(support(v));}
          moves[radius].push_back(std::move(local));}}
      for(bool adaptive:{false,true})for(std::string selection:{"cost","class_mass"}){
        AccuracyConfig c;c.init_family=c.band_family="huf";c.K=4;c.radius=2;c.adaptive=adaptive;c.selection=selection;c.audit=true;
        AccuracyDecoder decoder(n,cs,ls,p,w,labels,4,c,moves);decoder.base.observable_count=2;bool fb=false;auto initial=decoder.base.cut(syndrome,fb);auto result=decoder.decode(syndrome);require(model.apply(result.correction)==syndrome);require(result.frame==decoder.base.frame(result.correction));require(decoder.solver_calls<=2);
        if(selection=="cost"){double before=0,after=0;for(int j=0;j<m;++j){before+=w[j]*initial[j];after+=w[j]*result.correction[j];}require(after<=before+1e-9);require(decoder.higher_cost_updates==0);}
        decoder.decode(Bytes(n,0));require(decoder.decode(syndrome).correction==result.correction);++cases;
        c.joint=true;c.adaptive=false;AccuracyDecoder joint(n,cs,ls,p,w,labels,4,c,moves);joint.base.observable_count=2;
        auto j=joint.decode(syndrome);require(model.apply(j.correction)==syndrome);require(joint.solver_calls==0);++cases;
      }
    }
    // Disjoint persistent merges preserve exact witness residual invariant.
    Basis a({0}),b({2});a.insert({0,1},0);b.insert({2,3},1);a.merge(std::move(b));
    unsigned image=0;for(int j:a.witness)image^=(j==0?3:12);require((image^mask(a.residual))==5);
    std::cout<<"{\"status\":\"PASS\",\"exhaustive_and_seeded_cases\":"<<cases<<"}\n";
}
