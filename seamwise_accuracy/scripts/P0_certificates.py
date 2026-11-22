"""Supplement old-module growth support and initial BP certificates, no CP re-solving."""
import sys,pathlib,json,collections
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from gf2 import LogicalImage,span,reduce,mask
from decoders import logical_freedom
from _accuracy_native import LocalSolver
pin();out=ROOT/json.loads((ROOT/'results/failure_attribution/current_run.json').read_text())['path'];records=[json.loads(s) for s in (out/'failure_oracle_results.jsonl').read_text().splitlines()];dest=out/'growth_exposure_certificates.jsonl'
if dest.exists():raise RuntimeError('Refusing to overwrite growth certificates')
rank_checks=[]
for work in WORKS:
 a=model(work);w=np.log((1-a['p'])/a['p']);prepared={};original=native(a,'repair1');global_solver=LocalSolver(a['d'].shape[0],supports(a['d']),a['p'].tolist(),w.tolist())
 for radius in [1,2]:
  for bi,win in enumerate(native(a,'repair'+str(radius)).bands()):
   cols=np.asarray(win['columns']);rows=np.asarray(win['rows']);d=a['d'][rows][:,cols].tocsr();l=a['l'][:,cols].tocsr();image=LogicalImage(d,l);rd,rho=logical_freedom(d,l);assert (rd,rho)==(image.detector_rank,image.rank)
   rank_checks.append(dict(workload=work,radius=radius,detector_rank=rd,logical_rank=rho,independent_row_column_elimination_agrees=True));prepared[radius,bi]=dict(cols=cols,d=d,l=l,image=image,solver=LocalSolver(d.shape[0],supports(d),a['p'][cols].tolist(),w[cols].tolist()))
 for r in [r for r in records if r['workload']==work]:
  s=unpack(r['syndrome']);truth=np.array(r['true_observables'],dtype=np.uint8);global_result=global_solver.solve(s);assert np.array_equal(global_result['correction'],unpack(r['joint']['correction']));initial=original.trace(s);assert np.array_equal(initial['initial'],unpack(r['direct_cut']['correction']))
  states=dict(initial=unpack(r['seamwise_initial']));
  for radius in [1,2]:states['after_radius'+str(radius)]=unpack(next(e['after'] for e in reversed(r['repair_events']) if e['radius']==radius))
  support=[]
  for q in r['queries']:
   p=prepared[q['radius'],q['band']];x=states[q['state']];old=x[p['cols']];target=np.asarray(p['d']@old%2,dtype=np.uint8);snap=p['solver'].solve(target);b=frame(a,x)^truth;exposed=p['image'].exposed(p['d'],p['l'],snap['exposed_cluster_columns'],b)
   assert exposed['rank']==q['exposed_logical_change_rank'] and exposed['fix_direction_in_span']==q['correct_direction_exposed']
   proposal_change=np.asarray(p['l']@(np.asarray(snap['correction'])^old)%2,dtype=np.uint8);candidate_mismatch=b^proposal_change
   affine=p['image'].exposed(p['d'],p['l'],snap['exposed_cluster_columns'],candidate_mismatch)
   llr=np.asarray(snap['llr']);support.append(dict(affine_correct_class_reachable=affine['fix_direction_in_span'],proposal_correct_class=not bool(np.any(candidate_mismatch)),state=q['state'],radius=q['radius'],band=q['band'],target=pack(target),exposed_cluster_columns=snap['exposed_cluster_columns'],logical_rank=exposed['rank'],specific_fix_direction_exposed=exposed['fix_direction_in_span'],bp_converged=snap['bp_converged'],zero_bypass=snap['zero_bypass'],bp_counts=snap['counts'],hard_residual_weight=snap['bp_hard_residual_weight'],huf_residual_weight=snap['huf_residual_weight'],llr_quantiles=np.quantile(llr,[0,.1,.5,.9,1]).tolist() if len(llr) else None))
  record=dict(workload=work,sample_id=r['sample_id'],initial_cut_solver_diagnostics=initial['cut_solver_diagnostics'],joint_bp=dict(counts=global_result['counts'],converged=global_result['bp_converged'],hard_residual_weight=global_result['bp_hard_residual_weight'],huf_residual_weight=global_result['huf_residual_weight'],llr_quantiles=np.quantile(global_result['llr'],[0,.1,.5,.9,1]).tolist() if len(global_result['llr']) else None),queries=support,source_module_sha256=sha(pathlib.Path(sys.modules['_accuracy_native'].__file__)))
  with dest.open('a') as f:f.write(json.dumps(record,default=serial)+'\n')
atomic(out/'independent_rank_crosscheck.json',rank_checks);ledger('P0 growth support certificates and independent row/column rank crosscheck','COMPLETE',shots=len(records))
