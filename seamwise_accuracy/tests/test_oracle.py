import sys,pathlib,itertools
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from gf2 import LogicalImage
from oracle import minimize
from scipy import sparse

def test_exhaustive_image_and_cost():
 rng=np.random.default_rng(20261110)
 for trial in range(30):
  m=int(rng.integers(1,9));n=int(rng.integers(0,5));q=3;d=sparse.csr_matrix(rng.integers(0,2,(n,m)));l=sparse.csr_matrix(rng.integers(0,2,(q,m)));image=LogicalImage(d,l);allx=np.array(list(itertools.product([0,1],repeat=m)),dtype=np.uint8)
  for b in itertools.product([0,1],repeat=q):
   w=image.witness(np.array(b));possible=[x for x in allx if not np.any(d@x%2) and np.array_equal(l@x%2,b)];assert (w is not None)==bool(possible)
   if w is not None:assert not np.any(d@w%2) and np.array_equal(l@w%2,b)
  target_x=allx[int(rng.integers(len(allx)))];mat=sparse.vstack([d,l],format='csr');target=np.asarray(mat@target_x%2,dtype=np.uint8);weights=rng.random(m)*4-1
  ans=minimize(mat,target,weights,target_x,2);costs=[float(weights@x) for x in allx if np.array_equal(mat@x%2,target)];opt=min(costs)
  assert ans['real_cost_lower_bound']<=opt+1e-9 and ans['real_cost_upper_bound']>=opt-1e-9
  assert abs(ans['raw_primal_cost']-opt)<1e-7
