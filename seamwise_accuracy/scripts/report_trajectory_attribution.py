"""Separate actual production selection events from final-state repair queries."""
import sys,pathlib,json,collections
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from scipy.stats import hypergeom
p0=ROOT/json.loads((ROOT/'results/failure_attribution/current_run.json').read_text())['path'];raw=[json.loads(s) for s in (p0/'failure_oracle_results.jsonl').read_text().splitlines()];pop=json.loads((p0/'paired_outcomes.json').read_text());records=[];summaries=[]
def ci(k,n,N,alpha):
 lo,hi=k,N-n+k
 while lo<hi:
  mid=(lo+hi)//2
  if hypergeom.sf(k-1,N,mid,n)>=alpha/2:hi=mid
  else:lo=mid+1
 lower=lo;lo,hi=k,N-n+k
 while lo<hi:
  mid=(lo+hi+1)//2
  if hypergeom.cdf(k,N,mid,n)>=alpha/2:lo=mid
  else:hi=mid-1
 return lower,lo
for r in raw:
 if r['paired_category'] not in ['seamwise_only','both_wrong']:continue
 radius=2 if r['workload'].startswith('bb') else 1;events=[e for e in r['repair_events'] if e['radius']==radius]
 rejected=[e for e in events if e['candidate_true_class'] and not e['accepted'] and not e['incumbent_true_class']];harmed=[e for e in events if e['incumbent_true_class'] and e['accepted'] and not e['candidate_true_class']]
 records.append(dict(workload=r['workload'],sample_id=r['sample_id'],paired_category=r['paired_category'],production_radius=radius,correct_proposal_rejected=bool(rejected),correct_incumbent_harmed=bool(harmed),actual_path_proposal_selection_failure=bool(rejected or harmed),event_witnesses=[dict(band=e['band'],oldcost=e['oldcost'],newcost=e['newcost'],accepted=e['accepted'],incumbent_true_class=e['incumbent_true_class'],candidate_true_class=e['candidate_true_class']) for e in rejected+harmed]))
lines=['# Actual production-path selection witnesses','','This scope differs from the final-incumbent conditional queries in REFINED_ATTRIBUTION.md. Here a correct incumbent produced by partitioned initialization is itself an available correction; accepting a wrong-class repair instead is a production selection failure. Rejecting a generated correct proposal while retaining a wrong incumbent is also a selection failure. Their union is counted per failed shot, never as disjoint population causes. These events do not certify that every correct-class solution is more expensive, and are not ACCEPTANCE_LIMITED optimum certificates.','','All B4 primaries have one actual production seam, so an accepted wrong-class update directly changes a correct cut initial correction into the recorded final failure. Original radius1/radius2 branches remain separate, and only the production radius is used in this table.','','| Workload | Production radius | Diagnosed failed shots | Correct proposal rejected | Correct incumbent harmed | Union | Weighted population estimate | Pointwise 95% bounds |','|---|---:|---:|---:|---:|---:|---:|---|']
for work in WORKS:
 rs=[r for r in records if r['workload']==work];strata=[s for s in ['seamwise_only','both_wrong'] if pop[work]['cells'][s]];total=sum(pop[work]['cells'][s] for s in strata);estimate=lo=hi=0
 for st in strata:
  rr=[r for r in rs if r['paired_category']==st];k=sum(r['actual_path_proposal_selection_failure'] for r in rr);n=len(rr);N=pop[work]['cells'][st];l,u=ci(k,n,N,.05/len(strata));estimate+=N*k/n;lo+=l;hi+=u
 v=dict(workload=work,production_radius=rs[0]['production_radius'],n=len(rs),correct_proposal_rejected=sum(r['correct_proposal_rejected'] for r in rs),correct_incumbent_harmed=sum(r['correct_incumbent_harmed'] for r in rs),selection_failure_union=sum(r['actual_path_proposal_selection_failure'] for r in rs),weighted_fraction=estimate/total,pointwise95_finite_population_bounds=[lo/total,hi/total]);summaries.append(v);lines.append(f"| {work} | {v['production_radius']} | {v['n']} | {v['correct_proposal_rejected']} | {v['correct_incumbent_harmed']} | {v['selection_failure_union']} | {100*v['weighted_fraction']:.1f}% | {100*lo/total:.1f}%–{100*hi/total:.1f}% |")
lines+=['','Finite-population bounds invert the hypergeometric distribution within the seeded uniform historical failure strata, with Bonferroni across strata. They are exploratory pointwise intervals, not simultaneous across all diagnostic properties. The enriched control corpus is not used as an unweighted population denominator. Exact IDs and before/after event witnesses are in `trajectory_selection_certificates.json`. The conditional query count and this actual-path count answer different questions; neither should silently replace the other.']
atomic(p0/'trajectory_selection_certificates.json',records);atomic(p0/'trajectory_selection_estimates.json',summaries);(ROOT/'results/failure_attribution/TRAJECTORY_SELECTION.md').write_text('\n'.join(lines)+'\n')
for name in ['FAILURE_DIAGNOSIS.md','REFINED_ATTRIBUTION.md']:
 p=ROOT/'results/failure_attribution'/name;note='\n\nActual production-path selection witnesses, including a correct cut incumbent harmed by a cheaper repair, are separately counted in [TRAJECTORY_SELECTION.md](TRAJECTORY_SELECTION.md). The final-state conditional proposal counts do not include every earlier trajectory event.\n'
 if note not in p.read_text():p.write_text(p.read_text()+note)
print(json.dumps(summaries,indent=2))
