"""Exploratory paired diagnosis. Truth enters only this offline evaluator/oracle."""
import sys,pathlib,time,json,collections,math,hashlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from gf2 import LogicalImage,span,reduce,mask
from oracle import minimize
from scipy import sparse
pin();start=time.monotonic();budget=json.loads((ROOT/'configs/budget.json').read_text());out=ROOT/'results/failure_attribution';out.mkdir(exist_ok=True)
run=out/time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());run.mkdir(exist_ok=False);paired_all={};chosen=[];records=[];oracle_time=0;fidelity=0
oldrun=OLD/'results/20261110T022011Z-accuracy-badcf04f'
rng=np.random.default_rng(915620261110)
for wi,work in enumerate(WORKS):
 def rows(backend):return {r['sample_id']:r for r in map(json.loads,(oldrun/(work+'__'+backend+'__r0')/'shots.jsonl').read_text().splitlines())}
 sw,tess=rows('seamwise_selected'),rows('tuned_tesseract');assert sw.keys()==tess.keys();strata=collections.defaultdict(list)
 for sid,r in sw.items():
  other=tess[sid];assert r['shot']==other['shot'];name='both_wrong' if r['logical_failure'] and other['logical_failure'] else 'seamwise_only' if r['logical_failure'] else 'tesseract_only' if other['logical_failure'] else 'both_correct';strata[name].append(sid)
 paired_all[work]=dict(n=len(sw),cells={k:len(strata[k]) for k in ['both_correct','seamwise_only','tesseract_only','both_wrong']},Seamwise_failure_rate=sum(r['logical_failure'] for r in sw.values())/len(sw),Tesseract_failure_rate=sum(r['logical_failure'] for r in tess.values())/len(tess),Seamwise_wilson95=wilson(sum(r['logical_failure'] for r in sw.values()),len(sw)),paired=paired([sw[s]['logical_failure'] for s in sorted(sw)],[tess[s]['logical_failure'] for s in sorted(sw)]))
 selected=[]
 for name,limit in [('seamwise_only',12),('both_correct',8),('tesseract_only',8),('both_wrong',4)]:
  ids=sorted(strata[name]);selected.extend((name,ids[int(i)]) for i in rng.choice(len(ids),min(limit,len(ids)),replace=False))
 a=model(work);weights=np.log((1-a['p'])/a['p']);raw=np.load(OLD/DATA['workloads'][work]['splits']['test']['path']);images={};solvers={};plans={}
 from _accuracy_native import LocalSolver
 for radius in [1,2]:
  decoder=native(a,'repair'+str(radius));plans[radius]=decoder
  for bi,win in enumerate(decoder.bands()):
   cols=np.array(win['columns'],dtype=int);rows0=np.array(win['rows'],dtype=int);d=a['d'][rows0][:,cols].tocsr();l=a['l'][:,cols].tocsr();key=(radius,bi)
   images[key]=dict(cols=cols,rows=rows0,d=d,l=l,image=LogicalImage(d,l));solvers[key]=LocalSolver(d.shape[0],supports(d),a['p'][cols].tolist(),weights[cols].tolist())
 chosen_policy='repair2' if work.startswith('bb') else 'repair1';baseline=make(a,dict(kind='native',family='bphuf',policy=chosen_policy,persistent=True));joint=make(a,dict(kind='native',family='bphuf',policy='joint',persistent=True))
 atomic(run/(work+'_plans.json'),{f'r{r}_b{b}':dict(columns=v['cols'],rows=v['rows'],actual_logical_change_rank=v['image'].rank,detector_rank=v['image'].detector_rank) for (r,b),v in images.items()})
 for category,sid in selected:
  idx=sw[sid]['shot'];s=raw['detectors'][idx];truth=raw['observables'][idx];traces={radius:plans[radius].trace(s) for radius in [1,2]};selected_trace=traces[int(chosen_policy[-1])]
  xf=np.asarray(selected_trace['correction'],dtype=np.uint8);frame0,x0=baseline.decode(s);assert np.array_equal(xf,x0) and np.array_equal(frame0,selected_trace['frame']);assert hashlib.sha256(xf.tobytes()).hexdigest()==sw[sid]['correction_sha256'];fidelity+=1
  jf,jx=joint.decode(s);initial=np.asarray(selected_trace['initial']);assert valid(a,initial,s) and valid(a,xf,s) and valid(a,jx,s)
  events=[]
  for radius,tr in traces.items():
   for ev in tr['events']:
    bi=ev['band_index'];v=images[(radius,bi)];candidate=np.asarray(ev['before']).copy();candidate[v['cols']]=ev['candidate'];before_frame=frame(a,np.asarray(ev['before']));candidate_frame=frame(a,candidate)
    events.append(dict(radius=radius,band=bi,incumbent=pack(ev['incumbent']),candidate=pack(ev['candidate']),before=pack(ev['before']),after=pack(ev['after']),oldcost=ev['oldcost'],newcost=ev['newcost'],consistent=ev['consistent'],accepted=ev['accepted'],candidate_true_class=bool(np.array_equal(candidate_frame,truth)),incumbent_true_class=bool(np.array_equal(before_frame,truth)),actual_proposal_selection_failure=bool((np.array_equal(candidate_frame,truth) and not ev['accepted'] and not np.array_equal(before_frame,truth)) or (np.array_equal(before_frame,truth) and ev['accepted'] and not np.array_equal(candidate_frame,truth))),solver_ns=ev['solver_ns'],bp=ev['solver']['counts'],bp_hard_residual_weight=ev['solver']['bp_hard_residual_weight'],huf_residual_weight=ev['solver']['huf_residual_weight'],llr_statistics=dict(available=bool(len(ev['solver']['llr'])),quantiles=np.quantile(ev['solver']['llr'],[0,.1,.5,.9,1]).tolist() if len(ev['solver']['llr']) else None)))
  # The B=4/core=2 primary circuits have one seam. Union/radius2 are identical.
  states={'initial':initial,'after_radius1':np.asarray(traces[1]['correction']),'after_radius2':np.asarray(traces[2]['correction'])};oracle_cache={};queries=[]
  for state_name,x in states.items():
   b=frame(a,x)^truth;wrong=bool(np.any(b))
   for key,v in images.items():
    radius,bi=key;cols=v['cols'];d,l=v['d'],v['l'];old=x[cols];target=np.asarray(d@old%2,dtype=np.uint8);local=solvers[key].solve(target);candidate=np.asarray(local['correction']);assert np.array_equal(d@candidate%2,target)
    exposed=v['image'].exposed(d,l,local['exposed_cluster_columns'],b);witness=v['image'].witness(b);inc=float(weights[cols]@old);flags=[]
    if wrong and witness is None:flags.append('BAND_UNREACHABLE')
    if wrong and witness is not None and not exposed['fix_direction_in_span']:flags.append('REACH_EXPOSURE_LIMITED')
    result=dict(status='INFEASIBLE',feasibility='EXACT_GF2_INFEASIBLE') if witness is None else dict(status='FEASIBLE_NOT_PROVEN_OPTIMAL',feasibility='EXACT_GF2_FEASIBLE',optimization_termination='NOT_RUN_BUDGET_OR_CONTROL')
    if witness is not None:
     z=old^witness;assert np.array_equal(d@z%2,target) and np.array_equal(l@(z^old)%2,b)
     result.update(real_cost_upper_bound=float(weights[cols]@z),raw_primal_cost=float(weights[cols]@z),correction=pack(z))
     target_l=np.asarray(l@old%2,dtype=np.uint8)^b;cache_key=(key,target.tobytes(),target_l.tobytes())
     if cache_key in oracle_cache:result=dict(oracle_cache[cache_key],cached=True)
     elif wrong and oracle_time<budget['oracle_aggregate_wall_s'] and time.monotonic()-start<budget['P0_wall_s']:
      mat=sparse.vstack([d,l],format='csr');ans=minimize(mat,np.r_[target,target_l],weights[cols],z,min(budget['oracle_individual_wall_s'],budget['oracle_aggregate_wall_s']-oracle_time));oracle_time+=ans['elapsed_s'];ans['correction']=pack(ans['correction']);result.update(ans);oracle_cache[cache_key]=dict(result)
     if wrong and result.get('real_cost_upper_bound',math.inf)<inc-1e-10:flags.append('SEARCH_LIMITED')
     if wrong and result.get('real_cost_lower_bound',-math.inf)>=inc-1e-10:flags.append('ACCEPTANCE_LIMITED')
    full_candidate=x.copy();full_candidate[cols]=candidate;candidate_correct=bool(np.array_equal(frame(a,full_candidate),truth));newcost=float(weights[cols]@candidate)
    if wrong and candidate_correct and newcost>=inc-1e-10:flags.append('PROPOSAL_SELECTION_FAILURE')
    if wrong and not any(f in flags for f in ['BAND_UNREACHABLE','SEARCH_LIMITED','ACCEPTANCE_LIMITED']):flags.append('UNRESOLVED')
    query=dict(state=state_name,radius=radius,band=bi,incumbent_wrong=wrong,mismatch=b.tolist(),actual_logical_change_rank=v['image'].rank,exposed_logical_change_rank=exposed['rank'],correct_direction_exposed=exposed['fix_direction_in_span'],incumbent_cost=inc,local_proposal_cost=newcost,local_proposal_true_class=candidate_correct,local_proposal=pack(candidate),local_valid=bool(local['valid']),bp_counts=local['counts'],oracle=result,flags=flags);queries.append(query)
  record=dict(workload=work,sample_id=sid,old_sample_index=idx,paired_category=category,true_observables=truth.tolist(),syndrome=pack(s),joint=dict(correction=pack(jx),frame=np.asarray(jf).tolist()),direct_cut=dict(correction=pack(initial),frame=frame(a,initial).tolist()),seamwise_initial=pack(initial),seamwise_final=pack(xf),seamwise_final_frame=frame(a,xf).tolist(),tesseract_prediction=tess[sid]['prediction'],valid=True,fallback=selected_trace['fallback'],initial_stage_ns=selected_trace['initial_ns'],repair_events=events,queries=queries,combined_band_note='B=4/core=2 has one seam; union of radius1 and radius2 equals radius2, not another independent experiment',scope='EXPLORATORY_OFFLINE_TRUTH_ACCESS; no production candidate generation or runtime policy sees these labels')
  with (run/'failure_oracle_results.jsonl').open('a') as f:f.write(json.dumps(record,default=serial)+'\n')
  records.append(record);print(work,category,idx,'complete; oracle seconds',round(oracle_time,1),flush=True)
  atomic(run/'progress.json',dict(shots=len(records),native_trace_exact_matches=fidelity,oracle_wall_s=oracle_time,elapsed_s=time.monotonic()-start))
atomic(run/'paired_outcomes.json',paired_all);atomic(out/'current_run.json',dict(path=str(run.relative_to(ROOT)),status='COMPLETE',shots=len(records),native_trace_exact_matches=fidelity));ledger('P0 failure attribution','COMPLETE',run=str(run.relative_to(ROOT)),shots=len(records),oracle_wall_s=oracle_time)
