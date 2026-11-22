#include "seamwise/decoder.hpp"
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
PYBIND11_MODULE(_native,m){
    m.attr("build_contract")="C++20; fidelity; -fno-fast-math -ffp-contract=off; terminal-rebuild policy";
    py::class_<Decoder>(m,"Decoder")
      .def_readwrite("observable_count",&Decoder::observable_count)
      .def(py::init<int,std::vector<Support>,std::vector<Support>,std::vector<double>,std::vector<double>,Support,int,std::string,bool,std::string,bool,int,int,bool>(),
       py::arg("rows"),py::arg("columns"),py::arg("logical_columns"),py::arg("probabilities"),py::arg("weights"),py::arg("labels"),py::arg("blocks"),py::arg("family")="bphuf",py::arg("persistent")=true,py::arg("policy")="repair1",py::arg("audit")=false,py::arg("iterations")=30,py::arg("order")=0,py::arg("dense_terminal")=false)
      .def("decode",[](Decoder&d,py::array_t<uint8_t,py::array::c_style|py::array::forcecast>s){auto input=bits(s);Result r;{py::gil_scoped_release release;r=d.decode(input);}return py::make_tuple(arr(r.frame),arr(r.correction));})
      .def("decode_audit",[](Decoder&d,py::array_t<uint8_t,py::array::c_style|py::array::forcecast>s){auto r=d.decode(bits(s));py::dict out;out["frame"]=arr(r.frame);out["correction"]=arr(r.correction);out["fallback"]=r.fallback;py::list ev;for(auto&e:r.events){py::dict a;a["seam"]=e.seam;a["consistent"]=e.consistent;a["accepted"]=e.accepted;a["oldcost"]=e.oldcost;a["newcost"]=e.newcost;ev.append(a);}out["events"]=ev;return out;})
      .def("diagnostics",[](Decoder&d){py::dict out;out["wrapper"]=counters(d.counts);py::list ss;for(auto*s:d.solvers()){py::dict v;v["counts"]=counters(s->counts);v["detectors"]=s->model.n;v["faults"]=s->model.m;v["incidences"]=s->model.edges.size();py::list hh;for(const auto&h:s->histories){py::dict t;t["merge_sizes"]=h.merge_sizes;t["merge_detectors"]=h.merge_detectors;t["merge_faults"]=h.merge_faults;t["merge_incidences"]=h.merge_incidences;t["final_ranks"]=h.final_ranks;t["semantic_merges"]=h.semantic_merges;t["success"]=h.success;t["bp_converged"]=h.bp_converged;hh.append(t);}v["histories"]=hh;v["last_llr"]=s->last_llr;v["workspace_capacity_payload_bytes"]=s->workspace_bytes();ss.append(v);}out["solvers"]=ss;out["prepared_capacity_payload_bytes"]=d.prepared_bytes();return out;})
      .def("clear_diagnostics",[](Decoder&d){d.counts={};for(auto*s:d.solvers()){s->counts={};s->histories.clear();}});
    m.def("echo",[](py::array_t<uint8_t,py::array::c_style|py::array::forcecast>s){return arr(bits(s));});
}
