"""Read-only historical audit; run before the native rewrite."""
import importlib.metadata
import importlib.util
import json
import os
import pathlib
import platform
import subprocess
import sys
import time
from .common import ROOT, HIST, atomic, sha, load_model, pin

def environment():
    versions = {}
    for n in ["numpy", "scipy", "stim", "ldpc", "relay-bp", "tesseract-decoder", "pybind11"]:
        try: versions[n] = importlib.metadata.version(n)
        except importlib.metadata.PackageNotFoundError: versions[n] = "UNAVAILABLE"
    commands = {}
    for cmd in [["g++", "--version"], ["cmake", "--version"], ["rustc", "--version"], ["lscpu"], ["uname", "-a"]]:
        r = subprocess.run(cmd, capture_output=True, text=True)
        commands[" ".join(cmd)] = dict(returncode=r.returncode, stdout=r.stdout, stderr=r.stderr)
    cgroup = {}
    for p in ["/proc/self/cgroup", "/sys/fs/cgroup/cpu.max", "/sys/fs/cgroup/init.scope/cpu.max", "/sys/fs/cgroup/cpu.stat", "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor", "/sys/devices/system/cpu/cpu0/topology/thread_siblings_list"]:
        try: cgroup[p] = pathlib.Path(p).read_text()
        except OSError as e: cgroup[p] = str(e)
    commits = {}
    for p in (ROOT / "vendor").iterdir():
        if (p / ".git").exists():
            commits[p.name] = subprocess.check_output(["git", "-C", str(p), "rev-parse", "HEAD"], text=True).strip()
    binary_hashes={}
    for module in ["ldpc","relay_bp","tesseract_decoder","stim"]:
        spec=importlib.util.find_spec(module)
        if spec and spec.origin:
            path=pathlib.Path(spec.origin)
            files=[path] if path.suffix==".so" else list(path.parent.rglob("*.so"))
            for p in files:binary_hashes[str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)]=sha(p)
    for p in (ROOT/"build").glob("*.so"):binary_hashes[str(p.relative_to(ROOT))]=sha(p)
    return dict(python=sys.version, executable=sys.executable, platform=platform.platform(), versions=versions,binary_sha256=binary_hashes,
                commands=commands, cgroup=cgroup, commits=commits, affinity=list(os.sched_getaffinity(0)),
                loadavg=os.getloadavg(), resources="one pinned logical CPU; one decoder thread; batch=1; virtualized host; no bare-metal claim",
                captured_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

def matrix_audit(model):
    import numpy as np
    from scipy import sparse
    import stim
    d,l=model["d"].tocsc(),model["l"].tocsc()
    dem=stim.DetectorErrorModel.from_file(model["path"] / "detector_model.dem")
    columns=[]; logical=[]; priors=[]; separators=0
    for ins in dem.flattened():
        if ins.type != "error": continue
        ds=set();ls=set()
        for t in ins.targets_copy():
            if t.is_separator(): separators+=1
            elif t.is_relative_detector_id(): ds.symmetric_difference_update([t.val])
            elif t.is_logical_observable_id(): ls.symmetric_difference_update([t.val])
            else: raise ValueError(f"Unhandled DEM target {t}")
        columns.append(tuple(sorted(ds)));logical.append(tuple(sorted(ls)));priors.append(ins.args_copy()[0])
    dc=[tuple(map(int,d.indices[d.indptr[j]:d.indptr[j+1]])) for j in range(d.shape[1])]
    lc=[tuple(map(int,l.indices[l.indptr[j]:l.indptr[j+1]])) for j in range(l.shape[1])]
    assert columns==dc and logical==lc and np.array_equal(priors,model["p"])
    assert dem.num_detectors==d.shape[0] and dem.num_observables==l.shape[0]
    circuit=stim.Circuit.from_file(model["path"] / "circuit.stim")
    regenerated=circuit.detector_error_model(decompose_errors=False,approximate_disjoint_errors=False).flattened()
    assert str(regenerated)==str(dem.flattened())
    # Circuit noise contains mutually exclusive Pauli channels. Stim's DEM
    # conversion is the declared model; historical DEM samples are NOT
    # retroactively relabeled circuit samples. New samples use the circuit.
    raw=np.load(model["path"] / "samples.npz")
    assert np.array_equal((d@raw["errors"].T).T%2,raw["detectors"])
    assert np.array_equal((l@raw["errors"].T).T%2,raw["observables"])
    supports={}
    for ds,ls in zip(columns,logical): supports.setdefault(ds,set()).add(ls)
    invisible=[j for j in range(len(columns)) if not columns[j] and logical[j]]
    from scipy.sparse.csgraph import connected_components
    graph=sparse.bmat([[None,d],[d.T,None]],format="csr")
    nc,_=connected_components(graph,directed=False)
    return dict(status="PASS",detectors=d.shape[0],faults=d.shape[1],observables=l.shape[0],incidences=d.nnz,
                max_row_degree=int(d.tocsr().getnnz(axis=1).max()),max_column_degree=int(d.getnnz(axis=0).max()),
                zero_detector_logical_columns=invisible,duplicate_supports_distinct_logicals=sum(len(v)>1 for v in supports.values()),
                separators=separators,components=nc,dem_D_L_prior_exact=True,circuit_regenerated_dem_exact=True,
                historical_sampler="DEM independent mechanisms; a distinct experiment from circuit samples", hashes={p.name:sha(p) for p in model["path"].iterdir() if p.is_file()})

def historical_pairs(names, count=2):
    import numpy as np
    import decoders
    from huf import HUF
    from bp_huf import BPHUF
    records=[]
    for name in names:
        model=load_model(name);raw=np.load(model["path"] / "samples.npz")
        for bp in [False,True]:
            results=[];traces=[]
            for persistent in [False,True]:
                objects=[]
                def factory(a,p,unused):
                    h=(BPHUF if bp else HUF)(a,p,persistent);objects.append(h);return h
                saved=decoders.make_solver;decoders.make_solver=factory
                try:
                    st=decoders.Stack(model["d"],model["l"],model["p"],model["labels"],model["meta"]["blocks"],"reference")
                    st.prepare(["repair1"])
                    xs=[st.decode(s.astype(np.uint8),"repair1")[0] for s in raw["detectors"][:count]]
                    results.append(xs);traces.append([t for h in objects for t in h.stats])
                finally: decoders.make_solver=saved
            assert all(np.array_equal(a,b) for a,b in zip(*results))
            # Insertion counts intentionally differ; semantic growth must match.
            semantic=lambda ts:[(t["peak_cluster"],t["merge_sizes"],t["unions"]) for t in ts]
            assert semantic(traces[0])==semantic(traces[1])
            for pi,engine in enumerate((["BPHUF","BPSW"] if bp else ["HUF","SW"])):
                old=HIST / "results" / (name+"__"+engine+".npz")
                matches=None
                if old.exists():
                    stored=np.load(old)["corrections"][:count]
                    matches=all(np.array_equal(np.packbits(x,bitorder="little"),z) for x,z in zip(results[pi],stored))
                    assert matches
                records.append(dict(model=name,backend=engine,shots=count,corrections_match_pair=True,historical_match=matches,
                                    input_sha256=sha(model["path"] / "samples.npz"),independent_accuracy_samples=0))
    return records

def run_audit():
    pin()
    checks={}
    for manifest in ["source_manifest.json","input_manifest.json"]:
        old=json.loads((HIST/manifest).read_text())
        mismatches=[p for p,h in old.items() if not (HIST/p).exists() or sha(HIST/p)!=h]
        checks[manifest]=dict(files=len(old),mismatches=mismatches)
        assert not mismatches, mismatches
    names=["surface_d5_p0.006_B4","bb144_p0.015_B4","bb72_p0.015_B4"]
    report=dict(historical_hash_checks=checks,models={n:matrix_audit(load_model(n)) for n in names},
                paired_reproduction=historical_pairs(names[:2]))
    atomic(ROOT/"evidence"/"pre_rewrite_audit.json",report)
    atomic(ROOT/"evidence"/"environment.json",environment())
    print(json.dumps(report,indent=2))

if __name__=="__main__": run_audit()
