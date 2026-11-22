import sys,pathlib,json,collections,itertools
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from scipy.stats import hypergeom
out=ROOT/'results/failure_attribution';index=json.loads((out/'current_run.json').read_text());run=ROOT/index['path'];records=[json.loads(s) for s in (run/'failure_oracle_results.jsonl').read_text().splitlines()];paired_all=json.loads((run/'paired_outcomes.json').read_text())
flags=['BAND_UNREACHABLE','SEARCH_LIMITED','ACCEPTANCE_LIMITED','REACH_EXPOSURE_LIMITED','PROPOSAL_SELECTION_FAILURE','UNRESOLVED']
def hyper_ci(k,n,N,alpha):
 if n==0:return [0,N]
 low,high=k,N-n+k
 lo,hi=low,high
 while lo<hi:
  mid=(lo+hi)//2
  if hypergeom.sf(k-1,N,mid,n)>=alpha/2:hi=mid
  else:lo=mid+1
 lower=lo
 lo,hi=low,high
 while lo<hi:
  mid=(lo+hi+1)//2
  if hypergeom.cdf(k,N,mid,n)>=alpha/2:lo=mid
  else:hi=mid-1
 return [lower,lo]
lines=['# Failure attribution: exploratory evidence','',f"P0 run: `{index['path']}`. {len(records)} stratified diagnostic shots; native trace final corrections matched the unchanged archived decoder on all {index['native_trace_exact_matches']} shots. No invalid correction or model/numerical mismatch was observed in these checks; this is not a proof that every untested model/numerical issue is absent.",'','The old final-test corpus is now exploratory only. Truth is used solely for offline scoring and correct-class oracle constraints. Production proposal calls receive syndrome/conditioned detector targets, model priors and decoder-visible states only. New independent validation/timing/confirmatory streams were generated before policy changes.','','## Full paired historical outcomes','','| Workload | N | Both correct | Seamwise only wrong | Tesseract only wrong | Both wrong |','|---|---:|---:|---:|---:|---:|']
for w,p in paired_all.items():
 c=p['cells'];lines.append(f"| {w} | {p['n']} | {c['both_correct']} | {c['seamwise_only']} | {c['tesseract_only']} | {c['both_wrong']} |")
lines+=['','Exact sample-ID pairing, Wilson intervals and paired discordance confidence bounds are retained in `'+str((run/'paired_outcomes.json').relative_to(ROOT))+'`. Aggregate differences were not used to infer cell counts.','','## Conditional classification at the original final state','','Counts below concern sampled Seamwise failures only, with overlapping labels. Radius1/radius2 queries use the SAME incumbent final state; original production radius is one on surface and two on BB144. All primaries have B=4/core=2, hence one seam and combined radius1+radius2 equals radius2. No independent combined-band sample is invented.','','| Workload | Radius | Sampled failures | Unreachable | Cheaper correct class found | Cost blocking certified | Missing correct direction in growth exposure | Correct proposal cost-rejected | Cost explanation unresolved |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
summary=[];estimates=[]
for work in WORKS:
 failures=[r for r in records if r['workload']==work and r['paired_category'] in ['seamwise_only','both_wrong']];state='after_radius2' if work.startswith('bb') else 'after_radius1'
 for radius in [1,2]:
  qs=[q for r in failures for q in r['queries'] if q['state']==state and q['radius']==radius];counts={f:sum(f in q['flags'] for q in qs) for f in flags};summary.append(dict(workload=work,radius=radius,n=len(qs),counts=counts,oracle_statuses=dict(collections.Counter(q['oracle']['status'] for q in qs))))
  lines.append('| '+work+' | '+str(radius)+' | '+str(len(qs))+' | '+' | '.join(str(counts[f]) for f in flags)+' |')
  for flag in flags:
   pop=paired_all[work]['cells'];strata=[s for s in ['seamwise_only','both_wrong'] if pop[s]];total=sum(pop[s] for s in strata);estimate=0;lo=0;hi=0
   for s in strata:
    selected=[r for r in failures if r['paired_category']==s];queries=[next(q for q in r['queries'] if q['state']==state and q['radius']==radius) for r in selected];k=sum(flag in q['flags'] for q in queries);n=len(queries);N=pop[s];ci=hyper_ci(k,n,N,.05/len(strata));estimate+=N*k/n if n else 0;lo+=ci[0];hi+=ci[1]
   estimates.append(dict(workload=work,radius=radius,flag=flag,estimated_fraction_among_historical_Seamwise_failures=estimate/total,pointwise95_finite_population_bounds=[lo/total,hi/total],method='exact hypergeometric inversion within seeded simple-random outcome strata, Bonferroni across failure strata; not simultaneous across categories'))
lines+=['','`exposed_logical_change_rank` is the logical kernel image supported by columns activated inside actual HUF growth components, an algebraic upper bound on what that growth support exposes. It is not the number of candidates enumerated. REACH_EXPOSURE_LIMITED requires the specific true mismatch direction to be absent from this image while present in the full band image. Rank deficit alone is not called proof of a logical failure cause. A larger exposed rank does not prove an inexpensive correct correction exists.','','SEARCH_LIMITED requires an explicitly verified correct-class solution with strictly lower configuration cost. ACCEPTANCE_LIMITED requires a certified cost lower bound excluding strict descent. CP-SAT OPTIMAL refers to a floor-quantized integer objective; real-cost upper/lower bounds include its quantization error and a conservative floating summation allowance. Incomplete optimization is FEASIBLE_NOT_PROVEN_OPTIMAL/TIME_LIMIT, never infeasibility. Tiny brute-force tests verify feasibility, optimum and bound containment. See https://developers.google.com/optimization/cp/cp_solver/ and https://github.com/google/or-tools/blob/stable/ortools/sat/cp_model.proto .','','Pointwise finite-population interval estimates are in `classification_estimates.json`. The enriched failure/control corpus is not an unweighted estimate of population logical failure probability. Cost categories overlap exposure/selection categories; no forced exclusive causal explanation is asserted when certificates are missing.','','## Actual repair selection events','','| Workload | Radius | Diagnostic shots | Correct proposal rejected while incumbent wrong | Correct incumbent changed to wrong class |','|---|---:|---:|---:|---:|']
for work in WORKS:
 for radius in [1,2]:
  events=[e for r in records if r['workload']==work for e in r['repair_events'] if e['radius']==radius];rejected=[e for e in events if e['candidate_true_class'] and not e['accepted'] and not e['incumbent_true_class']];destroyed=[e for e in events if e['incumbent_true_class'] and e['accepted'] and not e['candidate_true_class']];lines.append(f'| {work} | {radius} | {len(events)} | {len(rejected)} | {len(destroyed)} |')
lines+=['','These are actual decisions in the native radius-specific traces, not aggregate subtraction. Controls include randomly selected successes and all available outcome types. Rejected correct proposals alone do not prove no cheaper correct-class solution exists. Correct incumbents harmed by a lower-cost proposal demonstrate configuration-cost/logical-outcome disagreement on those shots, not an exact posterior-MAP theorem.','','## Actionable next experiments','','The audit supplies positive search-limitation witnesses on surface d3, shows missing growth-supported logical directions, and records correct candidates rejected by cost descent and correct incumbents harmed by accepted lower-cost proposals. Therefore compare stronger conditional solvers and a bounded class-diverse candidate pool, and separately test monotone-cost versus truncated logical-class support selection. Do not assume more search or a wider band must improve accuracy. The cost optimum remains unresolved for most larger problems under the two-second cap; acceptance restrictions cannot yet be assigned a dominant population fraction.','','Representative IDs and complete correction/candidate/oracle certificates are in the run JSONL. The new policy must be selected on the new validation corpus and confirmed on unopened independent samples.']
atomic(run/'classification_counts.json',summary);atomic(run/'classification_estimates.json',estimates);(out/'FAILURE_DIAGNOSIS.md').write_text('\n'.join(lines)+'\n');print(out/'FAILURE_DIAGNOSIS.md')
