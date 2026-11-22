import pathlib,sys,json,hashlib,os,time,uuid
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1]
OLD=ROOT.parent/'seamwise_bench'
sys.path[:0]=[str(ROOT/os.environ.get('ACCURACY_NATIVE_BUILD','build_audit')),str(OLD/'python'),str(OLD/'build')]
from seamwise_bench.datasets import frozen_model
from seamwise_bench.adapters import supports,make
from seamwise_bench.analysis import wilson,paired
DATA=json.loads((OLD/'results/20261109T191912Z-dataset-43f9bff8/manifest.json').read_text())
WORKS=['surface_d3_p0.003_B4','surface_d5_p0.006_B4','bb144_p0.015_B4']
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def atomic(p,v):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,indent=2,default=serial)+'\n');os.replace(t,p)
def serial(v):
 if isinstance(v,np.ndarray):return v.tolist()
 if isinstance(v,np.generic):return v.item()
 raise TypeError(type(v).__name__)
def pin():
 cpu=min(os.sched_getaffinity(0));os.sched_setaffinity(0,{cpu});return cpu

def model(work):
 item=DATA['workloads'][work]
 for name,h in item['model_files'].items():
  if sha(OLD/item['path']/name)!=h:raise RuntimeError('MODEL_HASH_MISMATCH: '+work+'/'+name)
 return frozen_model(item)
def native(a,policy='repair1',family='bphuf',order=0,it=30):
 import _accuracy_native
 p=a['p'];obj=_accuracy_native.Decoder(a['d'].shape[0],supports(a['d']),supports(a['l']),p.tolist(),np.log((1-p)/p).tolist(),a['labels'].tolist(),a['meta']['blocks'],family,True,policy,True,it,order,False);obj.observable_count=a['l'].shape[0];return obj

def pack(x):return dict(bits=len(x),hex=np.packbits(np.asarray(x,dtype=np.uint8),bitorder='little').tobytes().hex())
def unpack(v):return np.unpackbits(np.frombuffer(bytes.fromhex(v['hex']),dtype=np.uint8),bitorder='little')[:v['bits']]
def frame(a,x):return np.asarray(a['l']@x%2,dtype=np.uint8)
def valid(a,x,s):return bool(np.array_equal(a['d']@x%2,s))
def ledger(action,status,**kw):
 p=ROOT/'results/EXECUTION_LEDGER.json';a=json.loads(p.read_text()) if p.exists() else [];a.append(dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),action=action,status=status,**kw));atomic(p,a)
