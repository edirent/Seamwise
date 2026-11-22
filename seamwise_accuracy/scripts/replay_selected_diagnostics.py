"""Fixed selected policies replayed on ALL original P0 cases, without tuning.
Decoder receives only model/syndrome. Offline clamping tests provide positive
conditional witnesses; a failed clamp is never called infeasibility.
"""
import sys,pathlib,json,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from freeze_guard import verify_lock
from runner import factory
assert json.loads((ROOT/'results/P4_run_index.json').read_text())['status']=='COMPLETE'
lock=verify_lock();pin();p0=ROOT/json.loads((ROOT/'results/failure_attribution/current_run.json').read_text())['path'];raw=[json.loads(s) for s in (p0/'failure_oracle_results.jsonl').read_text().splitlines()];dest=p0/'selected_policy_replay_certificates.jsonl';assert not dest.exists();records=[]
for work in WORKS:
 a=model(work);w=np.log((1-a['p'])/a['p']);cfg=next(c for c in lock['primary_configs'][work] if c['name']=='selected_combined');decoder=factory(a,cfg);plans=json.loads((p0/(work+'_plans.json')).read_text())
 for r in [r for r in raw if r['workload']==work]:
  s=unpack(r['syndrome']);t=time.monotonic();f,x=decoder.decode(s);elapsed=time.monotonic()-t;assert valid(a,x,s) and np.array_equal(frame(a,x),f);old=unpack(r['seamwise_final']);truth=np.array(r['true_observables'],dtype=np.uint8);checks=[]
  for key,plan in plans.items():
   cols=np.array(plan['columns']);clamped=old.copy();clamped[cols]=x[cols];isvalid=valid(a,clamped,s);correct=isvalid and np.array_equal(frame(a,clamped),truth);oc=float(w[cols]@old[cols]);nc=float(w[cols]@x[cols]);eps=2e-10*max(1,float(np.abs(w[cols]).sum()));cheaper=bool(correct and nc<oc-1e-10-eps)
   checks.append(dict(radius=int(key.split('_')[0][1:]),valid_clamped=bool(isvalid),clamped_correct_class=bool(correct),incumbent_cost=oc,clamped_cost=nc,cost_delta=nc-oc,floating_allowance=eps,cheaper_correct_witness=cheaper,clamped_correction=pack(clamped)))
  record=dict(workload=work,sample_id=r['sample_id'],paired_category=r['paired_category'],config=cfg,prediction=np.asarray(f).tolist(),correction=pack(x),new_logical_failure=bool(np.any(f!=truth)),full_cost=float(w@x),original_final_cost=float(w@old),conditional_witnesses=checks,diagnostic_elapsed_s=elapsed,scope='OFFLINE_FIXED_SELECTED_POLICY_REPLAY_ALL_84_P0_CASES; no choices or configurations changed')
  with dest.open('a') as out:out.write(json.dumps(record,default=serial)+'\n')
  records.append(record)
lines=['# Fixed selected-policy diagnostic replay','','After all performance/accuracy jobs finished, the exact frozen selected native configuration was replayed on all 84 original P0 cases. This is exploratory diagnostic evidence, not a new confirmatory cohort or additional parameter selection. All controls and failures remain recorded. Syndrome/frame validity is checked; labels only score already generated corrections.','','For each original failed incumbent and radius, the generated correction is clamped to the original exterior. A positive witness requires full syndrome validity, correct full logical frame, and a strictly cheaper conditional cost with a conservative floating allowance. An invalid clamp is not an infeasibility proof. These certificates supplement P0/P1; they do not retrospectively alter the initial audit or prove exact logical-class MAP.','','| Workload | Radius | Original failed diagnostic shots | Cheaper correct clamped witnesses |','|---|---:|---:|---:|']
summary=[]
for work in WORKS:
 rs=[r for r in records if r['workload']==work and r['paired_category'] in ['seamwise_only','both_wrong']]
 for radius in [1,2]:
  k=sum(q['cheaper_correct_witness'] for r in rs for q in r['conditional_witnesses'] if q['radius']==radius);summary.append(dict(workload=work,radius=radius,n=len(rs),cheaper_correct_witnesses=k));lines.append(f'| {work} | {radius} | {len(rs)} | {k} |')
lines+=['','The radius1 clamp preserves the original fixed exterior; whole-vector improvements outside that band are not misclassified as local search witnesses. Radius2 is the whole non-invisible primary region. Raw per-ID corrections/costs and unsuccessful clamps are in `selected_policy_replay_certificates.jsonl`. Counts are enriched diagnostic sample counts, not unweighted population percentages. This follow-up did not inspect truth to generate proposals and did not change any primary or secondary configuration.']
atomic(p0/'selected_policy_replay_summary.json',summary);(ROOT/'results/failure_attribution/SELECTED_POLICY_REPLAY.md').write_text('\n'.join(lines)+'\n');print(json.dumps(summary,indent=2))
