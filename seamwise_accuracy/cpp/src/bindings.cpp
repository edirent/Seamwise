#include "seamwise/decoder.hpp"
#include "seamwise/policy.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
namespace py=pybind11;
using namespace seamwise;
static py::array_t<uint8_t> arr(const Bytes&x){py::array_t<uint8_t>r(x.size());std::copy(x.begin(),x.end(),r.mutable_data());return r;}
static Bytes bits(py::array_t<uint8_t,py::array::c_style|py::array::forcecast>s){if(s.ndim()!=1)throw std::invalid_argument("syndrome must be 1D");return Bytes(s.data(),s.data()+s.size());}
static py::dict counters(const Counters&c){py::dict d;
#define FIELD(x) d[#x]=c.x
FIELD(roots);FIELD(eligibility_visits);FIELD(frontier_updates);FIELD(frontier_visits);FIELD(stale_heap);FIELD(insertions);FIELD(xor_entries);FIELD(xor_words);FIELD(dependent_columns);FIELD(merges);FIELD(activations);FIELD(state_initializations);FIELD(witness_bytes);FIELD(bp_ns);FIELD(growth_ns);FIELD(terminal_ns);FIELD(cut_ns);FIELD(repair_ns);FIELD(frame_ns);FIELD(fallback);FIELD(repair_calls);FIELD(accepted);FIELD(bp_iterations);FIELD(bp_converged);
#undef FIELD
return d;}
static void clear_solver(LocalSolver&s){s.counts={};s.histories.clear();s.last_llr.clear();}
static py::dict snapshot(LocalSolver&s,const Bytes&target){
    py::dict o;o["counts"]=counters(s.counts);o["llr"]=arr(Bytes{});
    o["llr"]=py::cast(s.last_llr);o["bp_converged"]=s.counts.bp_converged>0;o["zero_bypass"]=std::none_of(target.begin(),target.end(),[](uint8_t b){return b;});
    std::vector<Support>clusters;
    bool grew=std::any_of(s.histories.begin(),s.histories.end(),[](const History&h){return !h.bp_converged;});
    if(grew)for(int i=0;i<s.model.n+s.model.m;++i)if(s.parent[i]==i&&s.states[i]&&!s.states[i]->inserted.empty())clusters.push_back(s.states[i]->inserted);
    o["exposed_cluster_columns"]=clusters;o["target"]=arr(target);o["histories"]=s.histories.size();
    if(!s.last_llr.empty()){
        Bytes base(s.model.m),hard(s.model.m);for(int j=0;j<s.model.m;++j){base[j]=std::clamp(s.last_llr[j],-100.,100.)<0;hard[j]=s.last_llr[j]<=0;}
        auto residual=s.model.apply(base),bp_res=s.model.apply(hard);for(int i=0;i<s.model.n;++i){residual[i]^=target[i];bp_res[i]^=target[i];}
        o["huf_residual_weight"]=std::accumulate(residual.begin(),residual.end(),0);o["bp_hard_residual_weight"]=std::accumulate(bp_res.begin(),bp_res.end(),0);
    }else{o["huf_residual_weight"]=py::none();o["bp_hard_residual_weight"]=py::none();}
    return o;
}
static py::dict trace(Decoder&d,const Bytes&s){
    for(auto*solver:d.solvers())clear_solver(*solver);py::dict o;bool fb=false;auto t=std::chrono::steady_clock::now();auto x=d.cut(s,fb);
    o["initial_ns"]=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-t).count();o["initial"]=arr(x);o["initial_frame"]=arr(d.frame(x));o["fallback"]=fb;
    py::list cut;for(auto&win:d.cutplans)if(win.solver){py::dict q;q["counts"]=counters(win.solver->counts);q["llr"]=win.solver->last_llr;cut.append(q);}o["cut_solver_diagnostics"]=cut;
    py::list events;int bi=0;
    for(auto&win:d.bands){
        py::dict e;e["band_index"]=bi++;e["before"]=arr(x);Bytes old;double oc=0,nc=0;
        for(int j:win.columns){old.push_back(x[j]);oc+=d.model.weights[j]*x[j];}
        auto target=win.solver->model.apply(old);clear_solver(*win.solver);t=std::chrono::steady_clock::now();auto z=win.solver->decode(target);
        e["solver_ns"]=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-t).count();bool valid=win.solver->model.apply(z)==target;
        for(size_t k=0;k<z.size();++k)nc+=d.model.weights[win.columns[k]]*z[k];bool accept=valid&&nc<oc-1e-10;
        e["incumbent"]=arr(old);e["candidate"]=arr(z);e["oldcost"]=oc;e["newcost"]=nc;e["consistent"]=valid;e["accepted"]=accept;e["solver"]=snapshot(*win.solver,target);
        if(accept)for(size_t k=0;k<z.size();++k)x[win.columns[k]]=z[k];e["after"]=arr(x);events.append(e);
    }
    o["events"]=events;o["correction"]=arr(x);o["frame"]=arr(d.frame(x));return o;
}
PYBIND11_MODULE(_accuracy_native,m){
    py::class_<AccuracyDecoder>(m,"AccuracyDecoder",py::module_local())
      .def(py::init([](int n,std::vector<Support>d,std::vector<Support>l,std::vector<double>p,std::vector<double>w,Support labels,int blocks,py::dict config,std::map<int,std::vector<std::vector<Support>>>moves){
        AccuracyConfig c;
        auto integer=[&](const char*key,int value){return config.contains(key)?py::cast<int>(config[key]):value;};
        auto number=[&](const char*key,double value){return config.contains(key)?py::cast<double>(config[key]):value;};
        auto boolean=[&](const char*key,bool value){return config.contains(key)?py::cast<bool>(config[key]):value;};
        auto string=[&](const char*key,std::string value){return config.contains(key)?py::cast<std::string>(config[key]):value;};
        c.init_family=string("family","bphuf");c.band_family=string("band_family",c.init_family);c.selection=string("selection","cost");c.iterations=integer("iterations",30);c.band_iterations=integer("band_iterations",c.iterations);c.order=integer("band_order",integer("order",0));c.radius=integer("radius",1);c.K=integer("K",1);c.depth=integer("depth",2);c.max_calls=integer("max_calls",2);c.scale=number("scale",.625);c.damping=number("damping",0);c.weak_gap=number("weak_gap",.5);c.serial=string("schedule","parallel")=="serial";c.adaptive=boolean("adaptive",false);c.ensemble=boolean("ensemble",false);c.audit=boolean("audit",false);c.joint=boolean("joint",false);
        return std::make_unique<AccuracyDecoder>(n,std::move(d),std::move(l),std::move(p),std::move(w),std::move(labels),blocks,c,std::move(moves));
      }))
      .def_property("observable_count",[](AccuracyDecoder&d){return d.base.observable_count;},[](AccuracyDecoder&d,int q){d.base.observable_count=q;})
      .def("decode",[](AccuracyDecoder&d,py::array_t<uint8_t,py::array::c_style|py::array::forcecast>s){auto input=bits(s);Result r;{py::gil_scoped_release release;r=d.decode(input);}return py::make_tuple(arr(r.frame),arr(r.correction));})
      .def("stats",[](AccuracyDecoder&d){py::dict o;o["repair_solver_calls"]=d.solver_calls;o["escalations"]=d.escalations;o["generated_attempts"]=d.generated_attempts;o["accepted_updates"]=d.accepted_updates;o["higher_cost_updates"]=d.higher_cost_updates;o["logical_updates"]=d.logical_updates;o["peak_candidate_payload_lower_estimate_bytes"]=d.peak_candidate_payload;return o;})
      .def("memory",[](AccuracyDecoder&d){py::dict o;o["prepared_capacity_payload_bytes"]=d.prepared_bytes();o["workspace_capacity_payload_bytes"]=d.workspace_bytes();o["peak_candidate_payload_lower_estimate_bytes"]=d.peak_candidate_payload;return o;})
      .def("initial",[](AccuracyDecoder&d){return arr(d.initial_correction);})
      .def("events",[](AccuracyDecoder&d){py::list out;for(const auto&e:d.events){py::dict o;o["radius"]=e.radius;o["seam"]=e.seam;o["accessible_faults"]=e.accessible_faults;o["pool_rank"]=e.pool_rank;o["generated_rank"]=e.generated_rank;o["classes"]=e.classes;o["attempts"]=e.attempts;o["bp_converged"]=e.bp_converged;o["accepted"]=e.accepted;o["logical_changed"]=e.logical_changed;o["escalate_trigger"]=e.escalate;o["oldcost"]=e.oldcost;o["newcost"]=e.newcost;o["gap"]=e.gap;o["before_frame"]=arr(e.before_frame);o["after_frame"]=arr(e.after_frame);o["incumbent_signature"]=arr(e.incumbent_signature);py::list cc;for(const auto&c:e.candidates){py::dict v;v["correction"]=arr(c.x);v["logical_signature"]=arr(c.logical);v["cost"]=c.cost;cc.append(v);}o["candidates"]=cc;out.append(o);}return out;});

    py::class_<Decoder>(m,"Decoder",py::module_local())
      .def_readwrite("observable_count",&Decoder::observable_count)
      .def(py::init<int,std::vector<Support>,std::vector<Support>,std::vector<double>,std::vector<double>,Support,int,std::string,bool,std::string,bool,int,int,bool>(),py::arg("rows"),py::arg("columns"),py::arg("logical_columns"),py::arg("probabilities"),py::arg("weights"),py::arg("labels"),py::arg("blocks"),py::arg("family")="bphuf",py::arg("persistent")=true,py::arg("policy")="repair1",py::arg("audit")=true,py::arg("iterations")=30,py::arg("order")=0,py::arg("dense_terminal")=false)
      .def("decode",[](Decoder&d,py::array_t<uint8_t,py::array::c_style|py::array::forcecast>s){auto input=bits(s);Result r;{py::gil_scoped_release release;r=d.decode(input);}return py::make_tuple(arr(r.frame),arr(r.correction));})
      .def("configure_bp",[](Decoder&d,double scale,double damping,bool serial){for(auto*s:d.solvers())configure_bp(*s,scale,damping,serial);})
      .def("set_band_solver",[](Decoder&d,std::string family,int iterations,int order){for(auto&w:d.bands)if(w.solver)w.solver=std::make_unique<LocalSolver>(w.solver->model,family,true,d.audit,iterations,order);})
      .def("memory",[](Decoder&d){uint64_t workspace=0;for(auto*s:d.solvers())workspace+=s->workspace_bytes();py::dict out;out["prepared_capacity_payload_bytes"]=d.prepared_bytes();out["workspace_capacity_payload_bytes"]=workspace;return out;})
      .def("trace",[](Decoder&d,py::array_t<uint8_t,py::array::c_style|py::array::forcecast>s){return trace(d,bits(s));})
      .def("bands",[](Decoder&d){py::list out;for(auto&w:d.bands){py::dict v;v["columns"]=w.columns;v["rows"]=w.rows;out.append(v);}return out;});
    py::class_<LocalSolver>(m,"LocalSolver",py::module_local())
      .def(py::init([](int rows,std::vector<Support>cols,std::vector<double>p,std::vector<double>w,std::string family,int it,int order){return std::make_unique<LocalSolver>(Matrix(rows,std::move(cols),std::move(p),std::move(w)),family,true,true,it,order);}),py::arg("rows"),py::arg("columns"),py::arg("probabilities"),py::arg("weights"),py::arg("family")="bphuf",py::arg("iterations")=30,py::arg("order")=0)
      .def("configure_bp",[](LocalSolver&s,double scale,double damping,bool serial){configure_bp(s,scale,damping,serial);})
      .def("solve",[](LocalSolver&s,py::array_t<uint8_t,py::array::c_style|py::array::forcecast>input){auto target=bits(input);clear_solver(s);auto t=std::chrono::steady_clock::now();auto x=s.decode(target);auto elapsed=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-t).count();auto o=snapshot(s,target);o["correction"]=arr(x);o["valid"]=s.model.apply(x)==target;o["elapsed_ns"]=elapsed;return o;});
}
