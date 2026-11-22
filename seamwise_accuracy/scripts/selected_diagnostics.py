import sys,pathlib,json,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from runner import factory
from analysis import read_run
pin();assert not (ROOT/'configs/confirmatory_lock.json').exists()
p=ROOT/json.loads((ROOT/'results/finalists_current.json').read_text())['path'];ps,_=read_run(p);dest=ROOT/'results/selected_validation_diagnostics.jsonl';assert not dest.exists()
for work in WORKS:
 a=model(work);by={p['name']:p for p in ps if p['workload']==work};eligible=[by[k] for k in ['best_bp','stronger_solver','multi_candidate','adaptive_radius','best_combined']];minimum=min(q['failures'] for q in eligible);winner=min([q for q in eligible if q['failures']<=1.1*minimum],key=lambda q:q['mean_ms']);cfg=dict(winner['config'],name='selected_combined');obj=factory(a,cfg,audit=True)
 manifest=json.loads((ROOT/'results/new_samples/manifest.json').read_text());split=manifest['workloads'][work]['splits']['validation'];z=np.load(ROOT/split['path']);s=z['detectors'];obs=z['observables'];cache={}
 # Fixed-radius trace is explicitly a matched-BP diagnostic, not the adaptive execution trace.
 matched={k:v for k,v in cfg.items() if k not in ['candidate','adaptive','ensemble','joint','radius','K','selection','depth','max_calls']};bp=factory(a,matched,audit=True)
 for i in range(32):
  f,x=obj.decode(s[i]);assert valid(a,x,s[i]) and np.array_equal(frame(a,x),f);cache[i]=(np.array(f),np.array(x));events=list(obj.events()) if hasattr(obj,'events') else [];trace=bp.trace(s[i]);cut=trace['cut_solver_diagnostics'];band=[e['solver'] for e in trace['events']]
  def brief(q):
   llr=np.asarray(q.get('llr',[]));finite=llr[np.isfinite(llr)];return dict(counts=q['counts'],hard_residual_weight=q.get('bp_hard_residual_weight'),llr_finite=len(finite),llr_infinite=int(np.isinf(llr).sum()),llr_finite_quantiles=np.quantile(finite,[0,.1,.5,.9,1]).tolist() if len(finite) else None)
  r=dict(workload=work,shot=i,sample_id=split['sample_id_prefix']+':'+str(i),config=cfg,prediction=np.array(f).tolist(),logical_failure=bool(np.any(f!=obs[i])),native_work=dict(obj.stats()) if hasattr(obj,'stats') else None,actual_policy_events=events,matched_BP_fixed_radius_cut=[brief(q) for q in cut],matched_BP_fixed_radius_bands=[brief(q) for q in band])
  with dest.open('a') as out:out.write(json.dumps(r,default=serial)+'\n')
 for i in reversed(range(32)):
  f,x=obj.decode(s[i]);assert np.array_equal(f,cache[i][0]) and np.array_equal(x,cache[i][1])
ledger('Selected-policy audit and shuffled-shot validation','COMPLETE',shots_per_workload=32,source_module_sha256=sha(next((ROOT/'build_prod').glob('_accuracy_native*.so'))))
