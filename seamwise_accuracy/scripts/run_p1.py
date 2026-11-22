import sys,pathlib,json,time,collections
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from oracle import minimize
from local_research import pool,beam
from _accuracy_native import LocalSolver
pin();start=time.monotonic();p0=ROOT/json.loads((ROOT/'results/failure_attribution/current_run.json').read_text())['path'];records=[json.loads(s) for s in (p0/'failure_oracle_results.jsonl').read_text().splitlines()];out=ROOT/'results/solver_comparison'/time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());out.mkdir(parents=True,exist_ok=False)
results=[];preparations={};counts=collections.Counter()
for work in WORKS:
 a=model(work);w=np.log((1-a['p'])/a['p']);models={}
 for radius in [1,2]:
  for bi,win in enumerate(native(a,'repair'+str(radius)).bands()):
   cols=np.asarray(win['columns']);rows=np.asarray(win['rows']);d=a['d'][rows][:,cols].tocsr();l=a['l'][:,cols].tocsr();t=time.monotonic();moves,metadata=pool(d,l,w[cols]);preparations[work+':'+str(radius)]=dict(metadata,preparation_s=time.monotonic()-t)
   solvers={}
   for name,fam,order in [('HUF','bphuf',0),('LSD0','lsd',0),('LSD2','lsd',2),('OSD0','osd',0),('OSD2','osd',2)]:
    if name=='OSD2' and d.shape[1]>2500:continue
    solvers[name]=LocalSolver(d.shape[0],supports(d),a['p'][cols].tolist(),w[cols].tolist(),fam,30,order)
   models[radius,bi]=dict(cols=cols,rows=rows,d=d,l=l,moves=moves,solvers=solvers)
 for record in [r for r in records if r['workload']==work]:
  x=unpack(record['seamwise_final']);truth=np.array(record['true_observables'],dtype=np.uint8);b=frame(a,x)^truth;counts[work+record['paired_category']]+=1
  for (radius,bi),v in models.items():
   cols,d,l=v['cols'],v['d'],v['l'];old=x[cols];target=np.asarray(d@old%2,dtype=np.uint8);inc=float(w[cols]@old);row=dict(workload=work,sample_id=record['sample_id'],paired_category=record['paired_category'],radius=radius,band=bi,incumbent_cost=inc,incumbent=pack(old),conditioned_target=pack(target),candidates=[],unavailable=[])
   for name in ['HUF','LSD0','LSD2','OSD0','OSD2']:
    if name not in v['solvers']:row['unavailable'].append(dict(family=name,status='UNSUPPORTED',stage='predeclared_work_budget',reason='OSD order2 restricted to <=2500 conditioned fault variables in P1'));continue
    t=time.perf_counter_ns();ans=v['solvers'][name].solve(target);wall=time.perf_counter_ns()-t;z=np.asarray(ans['correction']);assert np.array_equal(d@z%2,target)
    row['candidates'].append(dict(family=name,correction=pack(z),configuration_cost=float(w[cols]@z),logical_signature=np.asarray(l@z%2,dtype=np.uint8).tolist(),correct_logical_class=bool(np.array_equal(l@(z^old)%2,b)),valid=True,native_solve_ns=ans['elapsed_ns'],binding_audit_wall_ns=wall,work_counters=ans['counts']))
   t=time.perf_counter_ns();zs,stats=beam(old,l,w[cols],v['moves']);elapsed=time.perf_counter_ns()-t;assert all(np.array_equal(d@z%2,target) for z in zs)
   for j,z in enumerate(zs):row['candidates'].append(dict(family='BEAM16',index=j,correction=pack(z),configuration_cost=float(w[cols]@z),logical_signature=np.asarray(l@z%2,dtype=np.uint8).tolist(),correct_logical_class=bool(np.array_equal(l@(z^old)%2,b)),valid=True,reference_beam_total_ns=elapsed,search_work=stats))
   # Exact cost oracle has no logical-class constraint and uses no truth.
   do_exact=record['paired_category'] in ['seamwise_only','both_correct'] and counts[work+record['paired_category']]<=3
   if do_exact:
    best=min([old]+[unpack(c['correction']) for c in row['candidates']],key=lambda z:float(w[cols]@z));opt=minimize(d,target,w[cols],best,2);opt['correction']=pack(opt['correction']);row['configuration_oracle']=opt
   else:row['configuration_oracle']=dict(status='UNSUPPORTED',stage='predeclared_oracle_subset_budget')
   row['distinct_feasible_candidates']=len({c['correction']['hex'] for c in row['candidates']});row['distinct_logical_signatures']=len({tuple(c['logical_signature']) for c in row['candidates']});row['cheaper_correct_alternative_found']=any(c['correct_logical_class'] and c['configuration_cost']<inc-1e-10 and c['family']!='HUF' for c in row['candidates'])
   with (out/'conditional_solver_results.jsonl').open('a') as f:f.write(json.dumps(row,default=serial)+'\n')
   results.append(row)
  print(work,record['paired_category'],record['old_sample_index'],'completed',len(results),'systems',flush=True)
atomic(out/'prepared_search_pools.json',preparations);atomic(ROOT/'results/solver_comparison/current_run.json',dict(path=str(out.relative_to(ROOT)),status='COMPLETE',conditioned_systems=len(results),elapsed_s=time.monotonic()-start));ledger('P1 identical conditioned local systems','COMPLETE',run=str(out.relative_to(ROOT)),systems=len(results),elapsed_s=time.monotonic()-start)
