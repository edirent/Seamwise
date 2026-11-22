import sys,pathlib,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from local_research import pool
pin();out=ROOT/'results/prepared_pools';out.mkdir(exist_ok=True);files={}
for work in WORKS:
 a=model(work);weights=np.log((1-a['p'])/a['p'])
 for radius in [1,2]:
  path=out/(work+'_r'+str(radius)+'.json')
  if path.exists():raise RuntimeError('Refusing to overwrite prepared pool')
  start=time.monotonic();bands=[]
  for win in native(a,'repair'+str(radius)).bands():
   cols=np.asarray(win['columns']);rows=np.asarray(win['rows']);d=a['d'][rows][:,cols].tocsr();l=a['l'][:,cols].tocsr();moves,metadata=pool(d,l,weights[cols]);bands.append(dict(columns=cols,rows=rows,moves=[m['indices'] for m in moves],metadata=metadata))
  atomic(path,dict(workload=work,model_hash=DATA['workloads'][work]['model_hash'],radius=radius,bands=bands,preparation_s=time.monotonic()-start,inputs='D,L,priors only; no sampled data or labels'));files[str(path.relative_to(ROOT))]=sha(path)
atomic(out/'manifest.json',dict(files=files,source='model-only fundamental detector-kernel moves; constructor independently verifies every D_J v=0'))
ledger('model-only candidate kernel preparation','COMPLETE',files=files)
