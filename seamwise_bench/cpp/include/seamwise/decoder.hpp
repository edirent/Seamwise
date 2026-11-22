#pragma once
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <map>
#include <memory>
#include <numeric>
#include <queue>
#include <string>
#include <vector>

namespace seamwise {
using Bytes=std::vector<uint8_t>;
using Support=std::vector<int>;
Support sx(const Support&,const Support&);
struct Counters {
    uint64_t roots=0,eligibility_visits=0,frontier_updates=0,frontier_visits=0,stale_heap=0;
    uint64_t insertions=0,xor_entries=0,xor_words=0,dependent_columns=0,merges=0,activations=0,state_initializations=0,witness_bytes=0;
    uint64_t bp_ns=0,growth_ns=0,terminal_ns=0,cut_ns=0,repair_ns=0,frame_ns=0;
    uint64_t fallback=0,repair_calls=0,accepted=0,bp_iterations=0,bp_converged=0;
};
struct Basis {
    struct Entry { Support column,witness; };
    std::map<int,Entry,std::greater<int>> pivots;
    Support residual,witness,inserted;
    explicit Basis(Support target={}):residual(std::move(target)){}
    void insert(const Support&,int,Counters* =nullptr);
    void merge(Basis&&,Counters* =nullptr);
};
struct Matrix {
    int n=0,m=0;
    std::vector<Support> columns,inc;
    std::vector<std::pair<int,int>> edges;
    std::vector<double> probabilities,weights;
    Matrix()=default;
    Matrix(int,std::vector<Support>,std::vector<double>,std::vector<double>);
    Bytes apply(const Bytes&) const;
    uint64_t storage_bytes() const;
};
struct History {
    Support merge_sizes;
    Support merge_detectors,merge_faults,merge_incidences,final_ranks;
    std::vector<Support> semantic_merges; // canonical labels and activated fault IDs
    bool success=false,bp_converged=false;
};
struct NativeBackend;
struct LocalSolver {
    const Matrix model;
    std::string family;
    bool persistent=false,bp_enabled=false,audit=false;
    bool dense_terminal=false;
    std::unique_ptr<NativeBackend> native;
    // Capacity survives shots; mutable state is reset before every call.
    std::vector<int> parent,size,label,head,tail,next,missing;
    std::vector<std::unique_ptr<Basis>> states;
    std::vector<Support> frontier;
    std::vector<uint8_t> materialized;
    std::vector<double> clocks,priority;
    Counters counts;
    std::vector<History> histories;
    std::vector<double> last_llr;
    LocalSolver(Matrix,std::string,bool=false,bool=false,int=30,int=0,bool=false);
    ~LocalSolver();
    Bytes decode(const Bytes&);
    Bytes grow(const Bytes&);
    int root(int);
    Basis& state(int,const Bytes&);
    const Support& boundary(int);
    Basis fresh(const Support&,const Support&);
    Support canonical(const Support&,const Support&);
    uint64_t workspace_bytes() const;
};
struct Window {
    Support columns,rows,core_rows;
    std::vector<uint8_t> commit;
    std::unique_ptr<LocalSolver> solver;
};
struct RepairEvent { int seam=0; bool consistent=false,accepted=false; double oldcost=0,newcost=0; };
struct Result { Bytes correction,frame; bool fallback=false; std::vector<RepairEvent> events; };
struct Decoder {
    const Matrix model;
    std::vector<Support> logical;
    Support labels,owner,zero;
    int blocks=0,core=2,observable_count=0;
    std::string family,policy;
    bool persistent=false,audit=false,dense_terminal=false;
    int iterations=30,order=0;
    std::unique_ptr<LocalSolver> global;
    std::vector<Window> cutplans,bands;
    Counters counts;
    Decoder(int,std::vector<Support>,std::vector<Support>,std::vector<double>,std::vector<double>,Support,int,std::string,bool,std::string,bool=false,int=30,int=0,bool=false);
    Window window(Support,Support);
    Bytes joint(const Bytes&);
    Bytes cut(const Bytes&,bool&);
    Result decode(const Bytes&);
    Bytes frame(const Bytes&) const;
    std::vector<LocalSolver*> solvers();
    uint64_t prepared_bytes() const;
};
}
