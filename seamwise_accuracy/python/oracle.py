"""Bounded CP-SAT integer objective with rigorous quantization bounds on C."""
import time,math
from fractions import Fraction
import numpy as np
from ortools.sat.python import cp_model
SCALE=100000000

def minimize(matrix,target,weights,hint,seconds=2):
 start=time.monotonic();a=matrix.tocsr();target=np.asarray(target,dtype=np.uint8);w=np.asarray(weights,dtype=float)
 # floor the exact rational represented by each IEEE weight, not a rounded product.
 q=np.array([(Fraction.from_float(float(v))*SCALE).__floor__() for v in w],dtype=np.int64)
 model=cp_model.CpModel();xs=[model.new_bool_var(str(j)) for j in range(a.shape[1])]
 for i in range(a.shape[0]):
  terms=[xs[int(j)] for j in a.indices[a.indptr[i]:a.indptr[i+1]]]
  if not target[i]:terms.append(True)
  model.add_bool_xor(terms)
 model.minimize(sum(int(c)*x for c,x in zip(q,xs)))
 for j,v in enumerate(hint):model.add_hint(xs[j],int(v))
 solver=cp_model.CpSolver();solver.parameters.num_search_workers=1;solver.parameters.random_seed=20261110;solver.parameters.max_time_in_seconds=max(.001,seconds-(time.monotonic()-start))
 status=solver.solve(model);name=solver.status_name(status);z=np.asarray(hint,dtype=np.uint8)
 assert np.array_equal(a@z%2,target),'GF2 hint is not feasible'
 if status in [cp_model.OPTIMAL,cp_model.FEASIBLE]:
  proposal=np.array([solver.value(x) for x in xs],dtype=np.uint8);assert np.array_equal(a@proposal%2,target)
  if float(w@proposal)<float(w@z):z=proposal
 if status==cp_model.MODEL_INVALID:raise AssertionError('CP-SAT model invalid')
 if status==cp_model.INFEASIBLE:raise AssertionError('CP-SAT infeasible contradicts verified GF2 hint')
 lower=(math.floor(solver.best_objective_bound-1e-6))/SCALE
 if status not in [cp_model.OPTIMAL,cp_model.FEASIBLE]:lower=sum(min(0,int(c)) for c in q)/SCALE
 if status==cp_model.OPTIMAL:lower=int(sum(int(c)*solver.value(x) for c,x in zip(q,xs)))/SCALE
 upper=float(w@z);eps=1e-10*max(1,float(np.abs(w).sum()))
 return dict(status='OPTIMAL' if status==cp_model.OPTIMAL else 'FEASIBLE_NOT_PROVEN_OPTIMAL',solver_status=name,
  optimization_termination='TIME_LIMIT_OR_OTHER_LIMIT' if status not in [cp_model.OPTIMAL,cp_model.INFEASIBLE] else name,
  real_cost_lower_bound=lower-eps,real_cost_upper_bound=upper+eps,raw_primal_cost=upper,quantization_scale=SCALE,
  optimality_scope='OPTIMAL refers to exact floor-quantized integer objective; real C bounds include quantization and conservative floating summation allowance',
  real_cost_gap_bound=upper+eps-(lower-eps),elapsed_s=time.monotonic()-start,branches=solver.num_branches,conflicts=solver.num_conflicts,correction=z)
