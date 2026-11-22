"""Derived finite-population estimates for corrected affine-exposure/P1 certificates."""
import sys,pathlib,json,collections
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from scipy.stats import hypergeom
p0=ROOT/json.loads((ROOT/'results/failure_attribution/current_run.json').read_text())['path'];p1=ROOT/json.loads((ROOT/'results/solver_comparison/current_run.json').read_text())['path'];records=json.loads((p1/'positive_failure_attribution_certificates.json').read_text());population=json.loads((p0/'paired_outcomes.json').read_text());estimates=[]
flags=['BAND_UNREACHABLE','SEARCH_LIMITED','ACCEPTANCE_LIMITED','REACH_EXPOSURE_LIMITED','PROPOSAL_SELECTION_FAILURE','UNRESOLVED']
def hyper_ci(k,n,N,alpha):
 if not n:return [0,N]
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
 return [lower,lo]
lines=['# Refined attribution after independent certificates','','This table supersedes the initial structural-span counts and initial SEARCH_LIMITED counts in FAILURE_DIAGNOSIS.md. The raw P0 file remains unchanged. Counts overlap; exposure absence is a structural search limitation, not proof that a cheap correct candidate exists or that it is the unique cause. Unresolved refers to absence of a certified cost explanation, not absence of every other label.','','| Workload | Radius | n failures sampled | Unreachable | Search witness | Cost blocking certified | Affine growth exposure missing | Proposal selection | Cost unresolved |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for work in WORKS:
 for radius in [1,2]:
  rows=[r for r in records if r['workload']==work and r['radius']==radius];counts={f:sum(f in r['augmented_flags'] for r in rows) for f in flags};lines.append('| '+work+' | '+str(radius)+' | '+str(len(rows))+' | '+' | '.join(str(counts[f]) for f in flags)+' |')
  for flag in flags:
   pop=population[work]['cells'];strata=[s for s in ['seamwise_only','both_wrong'] if pop[s]];total=sum(pop[s] for s in strata);estimate=lo=hi=0;ss=[]
   for st in strata:
    rs=[r for r in rows if r['paired_category']==st];k=sum(flag in r['augmented_flags'] for r in rs);n=len(rs);N=pop[st];bounds=hyper_ci(k,n,N,.05/len(strata));estimate+=N*k/n if n else 0;lo+=bounds[0];hi+=bounds[1];ss.append(dict(stratum=st,k=k,n=n,N=N,bounds=bounds))
   estimates.append(dict(workload=work,radius=radius,flag=flag,estimated_fraction_among_historical_Seamwise_failures=estimate/total,pointwise95_finite_population_bounds=[lo/total,hi/total],strata=ss,method='exact finite-population hypergeometric inversion; Bonferroni across failure strata, pointwise across labels'))
lines+=['','## Fractions among all historical Seamwise failures','','The diagnostic corpus intentionally oversamples rare paired outcomes. Estimates below weight each random failure stratum by its known historical population size. Intervals are pointwise 95% finite-population bounds, simultaneous across the two failure strata but not across all categories/radii. These are exploratory bounds for the ability of this audit to certify a property, with n=12 or 16 diagnostic failures; they are not precise estimates of a unique population cause.','','| Workload | Production radius | Property | Weighted estimate | 95% finite-population bounds |','|---|---:|---|---:|---|']
for work in WORKS:
 radius=2 if work.startswith('bb') else 1
 for e in [e for e in estimates if e['workload']==work and e['radius']==radius]:
  lo,hi=e['pointwise95_finite_population_bounds'];lines.append(f"| {work} | {radius} | {e['flag']} | {100*e['estimated_fraction_among_historical_Seamwise_failures']:.1f}% | {100*lo:.1f}%–{100*hi:.1f}% |")
lines+=['','No ACCEPTANCE_LIMITED optimum certificate was obtained in this sample; its estimated certificate frequency of zero does not establish the absence of cost blocking. Rejected correct proposals (P0 actual events) prove selection disagreement on those shots but do not exclude an even cheaper correct proposal. No MODEL_OR_NUMERICAL_MISMATCH was observed in the recorded model/hash, BP reference, syndrome/frame and trace regression gates.','','Exact intersections are in `'+str((p1/'failure_category_intersections.json').relative_to(ROOT))+'`; no unsupported exclusive causal partition is imposed. Representative shot IDs, witnesses, native costs, and original oracle intervals are preserved in the raw P0/P1 evidence.']
atomic(p1/'refined_classification_estimates.json',estimates);(ROOT/'results/failure_attribution/REFINED_ATTRIBUTION.md').write_text('\n'.join(lines)+'\n')
p=ROOT/'results/failure_attribution/FAILURE_DIAGNOSIS.md';txt=p.read_text();txt=txt.replace('## Conditional classification at the original final state','## Initial P0 classification (superseded by refined certificates)');notice='\n\nFinal classification and confidence intervals: [REFINED_ATTRIBUTION.md](REFINED_ATTRIBUTION.md). Its proposal-relative affine exposure test and P1 positive witnesses supersede the initial counts above.\n'
if notice not in txt:p.write_text(txt+notice)
# Explicit conditional Delta-C bounds, retaining all initial/sequential states.
raw=[json.loads(s) for s in (p0/'failure_oracle_results.jsonl').read_text().splitlines()];deltas=[]
for work in WORKS:
 a=model(work);w=np.log((1-a['p'])/a['p']);plans=json.loads((p0/(work+'_plans.json')).read_text());margins={int(k.split('_')[0][1:]):1e-10*max(1,float(np.abs(w[v['columns']]).sum())) for k,v in plans.items()}
 for r in [r for r in raw if r['workload']==work]:
  for q in r['queries']:
   o=q['oracle'];eps=margins[q['radius']];lo=o.get('real_cost_lower_bound');hi=o.get('real_cost_upper_bound');deltas.append(dict(workload=work,sample_id=r['sample_id'],state=q['state'],radius=q['radius'],status=o['status'],delta_C_star_lower_bound=None if lo is None else lo-q['incumbent_cost']-eps,delta_C_star_upper_bound=None if hi is None else hi-q['incumbent_cost']+eps,incumbent_floating_allowance=eps))
atomic(p0/'conditional_delta_cost_bounds.json',deltas)
