import sys,pathlib,json,collections,itertools
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
p0=ROOT/json.loads((ROOT/'results/failure_attribution/current_run.json').read_text())['path'];p1=ROOT/json.loads((ROOT/'results/solver_comparison/current_run.json').read_text())['path'];raw=[json.loads(s) for s in (p0/'failure_oracle_results.jsonl').read_text().splitlines()];local=[json.loads(s) for s in (p1/'conditional_solver_results.jsonl').read_text().splitlines()];certs=[json.loads(s) for s in (p0/'growth_exposure_certificates.jsonl').read_text().splitlines()];cert_lookup={(r['sample_id'],q['state'],q['radius']):q for r in certs for q in r['queries']};lookup={(r['sample_id'],r['radius']):r for r in local};records=[];intersections=[];tolerances={}
for work in WORKS:
 a=model(work);weights=np.log((1-a['p'])/a['p']);plans=json.loads((p0/(work+'_plans.json')).read_text())
 for key,plan in plans.items():tolerances[work,int(key.split('_')[0][1:])]=1e-10*max(1,float(np.abs(weights[plan['columns']]).sum()))
for r in raw:
 if r['paired_category'] not in ['seamwise_only','both_wrong']:continue
 state='after_radius2' if r['workload'].startswith('bb') else 'after_radius1'
 for q in [q for q in r['queries'] if q['state']==state]:
  alt=lookup[r['sample_id'],q['radius']];witnesses=[c for c in alt['candidates'] if c['correct_logical_class'] and c['configuration_cost']<alt['incumbent_cost']-1e-10-2*tolerances[r['workload'],q['radius']] and c['family']!='HUF'];flags=set(q['flags']);certificate=cert_lookup[r['sample_id'],state,q['radius']]
  flags.discard('REACH_EXPOSURE_LIMITED')
  if 'BAND_UNREACHABLE' not in flags and not certificate['affine_correct_class_reachable']:flags.add('REACH_EXPOSURE_LIMITED')
  if witnesses:
   assert 'ACCEPTANCE_LIMITED' not in flags,'Contradictory primal/dual certificates'
   flags.add('SEARCH_LIMITED');flags.discard('UNRESOLVED')
  records.append(dict(workload=r['workload'],sample_id=r['sample_id'],paired_category=r['paired_category'],radius=q['radius'],P0_flags=q['flags'],augmented_flags=sorted(flags),affine_growth_correct_class_reachable=certificate['affine_correct_class_reachable'],positive_cheaper_correct_witnesses=witnesses,incumbent_cost=alt['incumbent_cost']))
for work in WORKS:
 for radius in [1,2]:
  rows=[r for r in records if r['workload']==work and r['radius']==radius];counts=collections.Counter(tuple(r['augmented_flags']) for r in rows);intersections.append(dict(workload=work,radius=radius,n=len(rows),exact_intersections=[dict(flags=list(k),count=v) for k,v in counts.items()]))
atomic(p1/'positive_failure_attribution_certificates.json',records);atomic(p1/'failure_category_intersections.json',intersections)
lines=['','## Positive witness refinement from P1','','Alternative native/beam candidates are generated without truth and only scored by the offline evaluator. The following counts refine SEARCH_LIMITED when an explicitly verified correct-class candidate is cheaper than the original failed incumbent. They are positive witnesses, not an assumption that every unresolved case is search-limited.','','| Workload | Radius | Diagnosed failures | Cheaper correct witness after P1 |','|---|---:|---:|---:|']
for work in WORKS:
 for radius in [1,2]:
  rows=[r for r in records if r['workload']==work and r['radius']==radius];lines.append(f"| {work} | {radius} | {len(rows)} | {sum('SEARCH_LIMITED' in r['augmented_flags'] for r in rows)} |")
lines+=['','Growth exposure is corrected for the generated proposal affine base: a mismatch absent relative to the incumbent is not classified as unexposed if the proposal already reaches the correct class, or the growth-supported kernel can fix that proposal. The original raw structural-span flags remain auditable. Raw witnesses and all category intersections: `'+str(p1.relative_to(ROOT))+'/positive_failure_attribution_certificates.json` and `failure_category_intersections.json`. Growth-support certificates and independent row/column rank checks are in the P0 run. Unresolved optimization remains unresolved; no acceptance-blocking population claim is inferred from a rejected proposal alone.']
p=ROOT/'results/failure_attribution/FAILURE_DIAGNOSIS.md';p.write_text(p.read_text()+'\n'.join(lines)+'\n')
