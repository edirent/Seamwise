"""Unite P0/P1 witnesses with the fixed selected-policy follow-up, preserving history."""
import sys,pathlib,json,collections
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from scipy.stats import hypergeom
p0=ROOT/json.loads((ROOT/'results/failure_attribution/current_run.json').read_text())['path'];p1=ROOT/json.loads((ROOT/'results/solver_comparison/current_run.json').read_text())['path'];before=json.loads((p1/'positive_failure_attribution_certificates.json').read_text());follow=[json.loads(s) for s in (p0/'selected_policy_replay_certificates.jsonl').read_text().splitlines()];look={(r['sample_id'],q['radius']):q for r in follow for q in r['conditional_witnesses']};population=json.loads((p0/'paired_outcomes.json').read_text());records=[];estimates=[]
def ci(k,n,N,alpha):
 lo,hi=k,N-n+k
 while lo<hi:
  m=(lo+hi)//2
  if hypergeom.sf(k-1,N,m,n)>=alpha/2:hi=m
  else:lo=m+1
 lower=lo;lo,hi=k,N-n+k
 while lo<hi:
  m=(lo+hi+1)//2
  if hypergeom.cdf(k,N,m,n)>=alpha/2:lo=m
  else:hi=m-1
 return lower,lo
for r in before:
 q=look[r['sample_id'],r['radius']];flags=set(r['augmented_flags'])
 if q['cheaper_correct_witness']:
  assert not flags.intersection({'BAND_UNREACHABLE','ACCEPTANCE_LIMITED'}),'Primal/dual or GF2 contradiction'
  flags.add('SEARCH_LIMITED');flags.discard('UNRESOLVED')
 records.append(dict(r,final_flags=sorted(flags),selected_policy_positive_witness=q['cheaper_correct_witness']))
lines=['# Final diagnostic certificates, including the fixed-policy follow-up','','Initial P0 and P1 records are unchanged. This final table adds the selected-policy replay after the entire benchmark, with no policy tuning. A decoder-generated correction is clamped to the old exterior and counted only when its full syndrome/frame and strictly lower cost are independently verified. Evidence scopes and actual-path selection failures remain separate.','','| Workload | Radius | Sampled original failures | Unreachable | Cheaper correct witness, union | Missing original affine growth direction | Cost explanation unresolved |','|---|---:|---:|---:|---:|---:|---:|']
for work in WORKS:
 for radius in [1,2]:
  rs=[r for r in records if r['workload']==work and r['radius']==radius];count=lambda flag:sum(flag in r['final_flags'] for r in rs);lines.append(f"| {work} | {radius} | {len(rs)} | {count('BAND_UNREACHABLE')} | {count('SEARCH_LIMITED')} | {count('REACH_EXPOSURE_LIMITED')} | {count('UNRESOLVED')} |")
  pop=population[work]['cells'];strata=[s for s in ['seamwise_only','both_wrong'] if pop[s]];total=sum(pop[s] for s in strata);estimate=lo=hi=0
  for st in strata:
   ss=[r for r in rs if r['paired_category']==st];k=sum('SEARCH_LIMITED' in r['final_flags'] for r in ss);n=len(ss);N=pop[st];l,u=ci(k,n,N,.05/len(strata));estimate+=N*k/n;lo+=l;hi+=u
  estimates.append(dict(workload=work,radius=radius,n=len(rs),search_limited_certificates=count('SEARCH_LIMITED'),weighted_positive_witness_fraction=estimate/total,pointwise95_finite_population_bounds_for_certificate_frequency=[lo/total,hi/total],exclusive_intersections=[dict(flags=list(f),count=v) for f,v in collections.Counter(tuple(r['final_flags']) for r in rs).items()]))
lines+=['','## Production-radius search witnesses','','| Workload | Certified / sampled failures | Stratum-weighted witness fraction | Pointwise 95% finite-population bounds |','|---|---|---:|---|']
for e in estimates:
 if e['radius']!=(2 if e['workload'].startswith('bb') else 1):continue
 lo,hi=e['pointwise95_finite_population_bounds_for_certificate_frequency'];lines.append(f"| {e['workload']} | {e['search_limited_certificates']}/{e['n']} | {100*e['weighted_positive_witness_fraction']:.1f}% | {100*lo:.1f}%–{100*hi:.1f}% |")
lines+=['','The estimates weight seeded random historical failure strata and use exact hypergeometric inversion, Bonferroni across strata. They are exploratory pointwise intervals, not simultaneous across all categories. Positive witnesses certify existence; failure to find a witness does not certify absence, so an interval for the certificate rule must not be used as an upper bound on the actual prevalence of search limitation. Categories overlap and are not an exclusive causal partition.','','The decisive BB follow-up finds cheaper correct-class full-band corrections for all 12 sampled old failures using the unchanged selected damped-BP configuration. Thus strict cost descent permits a correct update on all 12: none of these 12 is ACCEPTANCE_LIMITED in the formal no-cheaper-correct-solution sense. The old solver missed such candidates, despite exact implementation agreement with official BP arithmetic. This supports inference/candidate generation as a limitation on these cases; the effect cannot be assigned separately to damping, normalization and iteration allowance without the controlled BP diagnostics. It does not prove that posterior-class mismatch never matters, or that every unsampled failure has the same cause.','','Actual-path selection conflicts still occurred in 7/12 BB cases (five correct initial corrections harmed; two correct proposals rejected). These can overlap SEARCH_LIMITED: an expensive correct proposal may be rejected even though another, cheaper correct correction exists. See `TRAJECTORY_SELECTION.md`. Raw selected corrections, clamped witnesses, floating allowances, original flags, new flags and exact label intersections remain in the accompanying JSON/JSONL.']
atomic(p0/'final_attribution_certificates.json',records);atomic(p0/'final_attribution_estimates.json',estimates);(ROOT/'results/failure_attribution/FINAL_ATTRIBUTION.md').write_text('\n'.join(lines)+'\n')
for name in ['FAILURE_DIAGNOSIS.md','REFINED_ATTRIBUTION.md']:
 p=ROOT/'results/failure_attribution'/name;note='\n\nThe later fixed selected-policy replay adds positive witnesses without changing any configuration. [FINAL_ATTRIBUTION.md](FINAL_ATTRIBUTION.md) gives the final union of certificates and intervals; initial P0/P1 counts above remain stage-specific.\n'
 if note not in p.read_text():p.write_text(p.read_text()+note)
print(json.dumps(estimates,indent=2))
