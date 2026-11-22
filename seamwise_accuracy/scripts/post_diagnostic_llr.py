"""Post-measurement P0 numeric audit. Never affects configuration selection."""
import sys,pathlib,json,collections
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from _accuracy_native import LocalSolver
from ldpc import BpDecoder
assert pathlib.Path(sys.modules['_accuracy_native'].__file__).parent.name=='build_audit'
assert json.loads((ROOT/'results/P4_run_index.json').read_text())['status'] in ['COMPLETE','ERROR']
pin();p0=ROOT/json.loads((ROOT/'results/failure_attribution/current_run.json').read_text())['path'];records=[json.loads(s) for s in (p0/'failure_oracle_results.jsonl').read_text().splitlines()];dest=p0/'finite_LLR_reference_audit.jsonl';assert not dest.exists();counts=collections.Counter()
for work in WORKS:
 a=model(work);weights=np.log((1-a['p'])/a['p']);plans=json.loads((p0/(work+'_plans.json')).read_text());prepared={}
 for key,p in plans.items():
  radius=int(key.split('_')[0][1:]);cols=np.array(p['columns']);rows=np.array(p['rows']);d=a['d'][rows][:,cols].tocsr();prepared[radius]=dict(cols=cols,d=d,native=LocalSolver(d.shape[0],supports(d),a['p'][cols].tolist(),weights[cols].tolist()),reference=BpDecoder(d,error_channel=a['p'][cols],max_iter=30,bp_method='minimum_sum',ms_scaling_factor=.625,schedule='parallel',input_vector_type='syndrome'))
 for r in [r for r in records if r['workload']==work]:
  states={'initial':unpack(r['seamwise_initial'])}
  for radius in [1,2]:states['after_radius'+str(radius)]=unpack(next(e['after'] for e in reversed(r['repair_events']) if e['radius']==radius))
  for q in r['queries']:
   p=prepared[q['radius']];target=np.asarray(p['d']@states[q['state']][p['cols']]%2,dtype=np.uint8);snap=p['native'].solve(target);llr=np.array(snap['llr']);zero=not bool(np.any(target));match=None;gap=None;reference_counts=None;agreement=None
   if not zero:
    p['reference'].decode(target);ref=np.asarray(p['reference'].log_prob_ratios);finite=np.isfinite(llr);match=bool(np.array_equal(finite,np.isfinite(ref)) and np.array_equal(np.isnan(llr),np.isnan(ref)) and np.array_equal(np.isposinf(llr),np.isposinf(ref)) and np.array_equal(np.isneginf(llr),np.isneginf(ref)) and np.array_equal(llr[finite],ref[finite]));gap=float(np.max(np.abs(llr[finite]-ref[finite]),initial=0));agreement=bool(np.array_equal(np.isfinite(llr),np.isfinite(ref)) and np.array_equal(np.isnan(llr),np.isnan(ref)) and np.array_equal(np.isposinf(llr),np.isposinf(ref)) and np.array_equal(np.isneginf(llr),np.isneginf(ref)) and np.allclose(llr[finite],ref[finite],rtol=1e-12,atol=1e-10));reference_counts=dict(nan=int(np.isnan(ref).sum()),positive_inf=int(np.isposinf(ref).sum()),negative_inf=int(np.isneginf(ref).sum()))
   finite=llr[np.isfinite(llr)];row=dict(workload=work,sample_id=r['sample_id'],state=q['state'],radius=q['radius'],zero_bypass=zero,llr_total=len(llr),finite=len(finite),nan=int(np.isnan(llr).sum()),positive_inf=int(np.isposinf(llr).sum()),negative_inf=int(np.isneginf(llr).sum()),finite_quantile_method='nearest avoids interpolation overflow',finite_quantiles=np.quantile(finite,[0,.1,.5,.9,1],method='nearest').tolist() if len(finite) else None,official_reference_exact=match,official_reference_agreement_rtol1e_12_atol1e_10=agreement,maximum_finite_reference_gap=gap,reference_nonfinite=reference_counts)
   counts[work,'queries']+=1;counts[work,'native_nan_values']+=row['nan'];counts[work,'infinite_values']+=row['positive_inf']+row['negative_inf'];counts[work,'strict_reference_difference']+=match is False;counts[work,'reference_mismatch_beyond_tolerance']+=agreement is False
   with dest.open('a') as f:f.write(json.dumps(row,allow_nan=False)+'\n')
atomic(p0/'finite_LLR_summary.json',[dict(workload=w,**{k:v for (ww,k),v in counts.items() if ww==w}) for w in WORKS])
# Portable derived copies label non-finite summary tokens; originals stay intact.
def portable(x):
 if isinstance(x,float) and not np.isfinite(x):return {'nonfinite_float':'NaN' if np.isnan(x) else '+Infinity' if x>0 else '-Infinity'}
 if isinstance(x,list):return [portable(y) for y in x]
 if isinstance(x,dict):return {k:portable(v) for k,v in x.items()}
 return x
for name in ['failure_oracle_results','growth_exposure_certificates']:
 src=p0/(name+'.jsonl');out=p0/(name+'.portable.jsonl');assert not out.exists()
 with out.open('x') as f:
  for line in src.read_text().splitlines():f.write(json.dumps(portable(json.loads(line)),allow_nan=False)+'\n')
print(json.dumps([dict(workload=w,**{k:v for (ww,k),v in counts.items() if ww==w}) for w in WORKS],indent=2))
