import json
import numpy as np
from scipy import sparse
from .common import ROOT,HIST,atomic,load_model,pin,unique_run
from .adapters import make

def event_projection(events):return [(e["seam"],bool(e["consistent"]),bool(e["accepted"])) for e in events]

def compare_model(model,ss,configs,out):
    rows=[]
    for cfg in configs:
        reference=make(model,dict(cfg,kind="python"),audit=True)
        native=make(model,dict(cfg,kind="native"),audit=True)
        for i,s in enumerate(ss):
            s=s.astype(np.uint8);yr,xr=reference.decode(s)
            xn=native.backend.decode_audit(s)
            if not np.array_equal(xr,xn["correction"]) or not np.array_equal(yr,xn["frame"]):
                np.savez(out/f"mismatch_{len(rows)}.npz",syndrome=s,reference=xr,native=xn["correction"])
                raise AssertionError(f"correction mismatch {model.get('name')} shot={i} {cfg}")
            fb,ev=reference.last
            assert fb==xn["fallback"] and event_projection(ev)==event_projection(xn["events"])
            assert np.array_equal(model["d"]@xr%2,s)
        diagnostics=native.backend.diagnostics()
        for ref,ns in zip(reference.objects,diagnostics["solvers"]):
            successful=[t for t in ns["histories"] if t["success"]]
            assert len(ref.stats)==len(successful),(cfg,len(ref.stats),len(successful))
            assert [t["merge_sizes"] for t in ref.stats]==[t["merge_sizes"] for t in successful],cfg
            assert ref.semantic_histories==[t["semantic_merges"] for t in successful if not t["bp_converged"]],cfg
            if cfg.get("family")=="bphuf" and successful:
                # Exact correction gates are strict. Report floating-point
                # diagnostics separately; tolerance never excuses a bit mismatch.
                if ref.bp is not None and len(ns["last_llr"]):
                    rr=np.asarray(ref.bp.log_prob_ratios);nn=np.asarray(ns["last_llr"])
                    assert np.array_equal(np.isfinite(rr),np.isfinite(nn))
                    assert np.array_equal(rr[~np.isfinite(rr)],nn[~np.isfinite(nn)])
                    gap=np.max(np.abs(rr[np.isfinite(rr)]-nn[np.isfinite(nn)]),initial=0.)
                    assert gap<1e-10,(cfg,gap)
        expected=[native.decode(s.astype(np.uint8))[1].copy() for s in ss]
        for j in reversed(range(len(ss))):assert np.array_equal(native.decode(ss[j].astype(np.uint8))[1],expected[j])
        perm=np.random.default_rng(1729).permutation(len(ss))
        for j in perm:assert np.array_equal(native.decode(ss[j].astype(np.uint8))[1],expected[j])
        fresh=make(model,dict(cfg,kind="native"))
        for j in range(len(ss)):assert np.array_equal(fresh.decode(ss[j].astype(np.uint8))[1],expected[j])
        native.backend.clear_diagnostics()
        rows.append(dict(config=cfg,shots=len(ss),exact_correction=True,repair_decisions=True,successful_growth_traces=True,semantic_event_ids_exact=True,
                         reset_reversed_shuffled_fresh=True))
    return rows

def run_fidelity(count=8):
    pin();out=unique_run("fidelity");rows=[]
    configs=[dict(family=f,persistent=p,policy="repair1",dense_terminal=d) for f in ["huf","bphuf"] for p in [False,True] for d in [False,True]]
    try:
        for name in ["surface_d3_p0.003_B4","surface_d5_p0.006_B4","bb144_p0.015_B4"]:
            if not (HIST/"data"/name).exists():
                if name.startswith("surface_d3"):name="surface_d3_p0.006_B4"
            model=load_model(name);model["name"]=name;ss=np.load(model["path"]/"samples.npz")["detectors"][:count]
            # Non-BP BB144 is expensive in the historical implementation;
            # it gets two fixtures while all BP variants get the full subset.
            for cfg in configs:
                selected=ss[:2] if name.startswith("bb") and cfg["family"]=="huf" else ss
                rows.append(dict(model=name,tests=compare_model(model,selected,[cfg],out)))
        atomic(out/"correctness.json",dict(status="PASS",tests=rows,independent_accuracy_samples=0))
        atomic(ROOT/"evidence"/"fidelity_gate.json",dict(status="PASS",run=str(out.relative_to(ROOT)),source_hashes=source_hashes()))
    except Exception as e:
        atomic(out/"correctness.json",dict(status="FAIL",error=repr(e),completed=rows))
        atomic(ROOT/"evidence"/"fidelity_gate.json",dict(status="FAIL",run=str(out.relative_to(ROOT)),error=repr(e)))
        raise
    print(out)
    return out

def source_hashes():
    from .common import sha
    return {str(p.relative_to(ROOT)):sha(p) for base in ["cpp","python"] for p in sorted((ROOT/base).rglob('*')) if p.is_file() and p.suffix in [".cpp",".hpp",".py"]}

if __name__=="__main__":run_fidelity()
