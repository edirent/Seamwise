import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
import stim
out=ROOT/'results/new_samples';out.mkdir(exist_ok=False);items={}
for wi,work in enumerate(WORKS):
 a=model(work);c=stim.Circuit.from_file(a['path']/'circuit.stim');dest=out/work;dest.mkdir();splits={}
 for split,n,base in [('validation',512,615620261110),('timing',1024,715620261110),('confirmatory',10000,815620261110)]:
  seed=base+wi*1000003;d,l=c.compile_detector_sampler(seed=seed).sample(shots=n,separate_observables=True);p=dest/(split+'.npz');np.savez_compressed(p,detectors=d.astype(np.uint8),observables=l.astype(np.uint8));splits[split]=dict(path=str(p.relative_to(ROOT)),sha256=sha(p),count=n,seed=seed,sample_id_prefix=DATA['workloads'][work]['model_hash']+':'+str(seed))
 items[work]=dict(model=DATA['workloads'][work],splits=splits)
atomic(out/'manifest.json',dict(kind='new_independent_circuit_samples',workloads=items,stim_version=stim.__version__,test_labels_opened=False,previous_test_status='EXPLORATORY_ONLY'))
ledger('new independently seeded circuit data preparation','COMPLETE',manifest=str((out/'manifest.json').relative_to(ROOT)))
