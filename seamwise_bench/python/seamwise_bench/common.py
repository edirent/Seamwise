import hashlib
import json
import os
import pathlib
import sys
import time
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[2]
HIST = ROOT.parent / "experiments"
sys.path[:0] = [str(HIST), str(HIST / "research"), str(ROOT / "build")]

class UnsupportedModel(ValueError):
    """An explicit adapter capability limit, distinct from a decoder bug."""

def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()

def atomic(path, value):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)

def unique_run(label):
    name = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + label + "-" + uuid.uuid4().hex[:8]
    p = ROOT / "results" / name
    p.mkdir(parents=True, exist_ok=False)
    return p

def load_model(name):
    import numpy as np
    from scipy import sparse
    p = HIST / "data" / name
    a = np.load(p / "metadata_arrays.npz")
    return dict(path=p, d=sparse.load_npz(p / "D.npz"), l=sparse.load_npz(p / "L.npz"),
                p=a["p"], labels=a["detector_blocks"], meta=json.loads((p / "model.json").read_text()))

def pin():
    allowed = sorted(os.sched_getaffinity(0))
    cpu = int(os.environ.get("SEAMWISE_CPU", allowed[0]))
    if cpu not in allowed:
        raise ValueError("Requested CPU outside allowed affinity")
    os.sched_setaffinity(0, {cpu})
    return cpu
