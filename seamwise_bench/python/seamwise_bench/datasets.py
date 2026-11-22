"""Circuit-sampled, disjoint splits with immutable content manifests."""
import json
import pathlib
import shutil
import numpy as np
import stim
from .common import ROOT,HIST,atomic,sha,digest,unique_run,load_model
from .audit import matrix_audit,environment

def prepare(config):
    out=unique_run("dataset");items={}
    for wi,name in enumerate(config["workloads"]):
        model=load_model(name);audit=matrix_audit(model)
        dest=out/name;dest.mkdir()
        for filename in ["circuit.stim","detector_model.dem","D.npz","L.npz","metadata_arrays.npz","model.json","code.npz"]:
            if (model["path"]/filename).exists():shutil.copyfile(model["path"]/filename,dest/filename)
        circuit=stim.Circuit.from_file(dest/"circuit.stim")
        modelhash=digest({k:sha(dest/k) for k in ["circuit.stim","detector_model.dem","D.npz","L.npz","metadata_arrays.npz"]})
        splits={}
        for split,count in config["samples"].items():
            # Seeds declared in config before any validation outcome is read.
            seed=int(config["seeds"][split])+wi*1000003
            det,obs=circuit.compile_detector_sampler(seed=seed).sample(shots=count,separate_observables=True)
            path=dest/(split+".npz")
            np.savez_compressed(path,detectors=det.astype(np.uint8),observables=obs.astype(np.uint8))
            splits[split]=dict(seed=seed,shots=count,sha256=sha(path),path=str(path.relative_to(ROOT)),
                               sample_id_prefix=f"{modelhash}:{seed}",sampler="stim.Circuit.compile_detector_sampler",bit_order="unpacked detector IDs; packbits little for hashes")
        items[name]=dict(model_hash=modelhash,path=str(dest.relative_to(ROOT)),splits=splits,audit=audit,
                         model_files={k.name:sha(k) for k in dest.iterdir() if k.suffix!=".npz" or k.name in ["D.npz","L.npz","code.npz","metadata_arrays.npz"]})
    manifest=dict(schema=1,kind="frozen_circuit_samples",config=config,workloads=items,environment=environment(),historical_inputs_untouched=True,
                  seed_policy="disjoint declared streams by split and workload; test labels unexamined until frozen policy evaluation")
    atomic(out/"manifest.json",manifest)
    (out/"manifest.sha256").write_text(sha(out/"manifest.json")+"  manifest.json\n")
    print(out/"manifest.json");return out/"manifest.json"

def verify_manifest(path):
    path=pathlib.Path(path);v=json.loads(path.read_text())
    if v.get("kind")=="frozen_campaign":
        data=verify_manifest(ROOT/v["dataset_manifest"])
        if digest(data)!=v["dataset_hash"]:raise ValueError("frozen campaign dataset digest changed")
        data["frozen_campaign"]=v
        return data
    for name,item in v["workloads"].items():
        base=ROOT/item["path"]
        for filename,h in item["model_files"].items():
            if sha(base/filename)!=h:raise ValueError(f"model hash changed: {name}/{filename}")
        for split,s in item["splits"].items():
            if sha(ROOT/s["path"])!=s["sha256"]:raise ValueError(f"sample hash changed: {name}/{split}")
    return v

def frozen_model(item):
    from scipy import sparse
    path=ROOT/item["path"];a=np.load(path/"metadata_arrays.npz")
    return dict(path=path,d=sparse.load_npz(path/"D.npz"),l=sparse.load_npz(path/"L.npz"),p=a["p"],labels=a["detector_blocks"],meta=json.loads((path/"model.json").read_text()))
