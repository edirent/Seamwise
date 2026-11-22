import sys,pathlib,json,math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from _accuracy_native import LocalSolver
from ldpc import BpDecoder
from scipy import sparse

def ref_bp(d,p,s,alpha,damping,iters):
 cols=supports(d);rows=[list(np.flatnonzero(d.toarray()[i])) for i in range(d.shape[0])];prior=[math.log((1-float(x))/float(x)) for x in p];v2c={(i,j):prior[j] for j,rs in enumerate(cols) for i in rs};c2v={key:0. for key in v2c};last=None
 for it in range(1,iters+1):
  old=dict(c2v)
  for i,js in enumerate(rows):
   total=int(s[i])+sum(v2c[i,j]<=0 for j in js);temp=float(np.finfo(float).max)
   for j in js:c2v[i,j]=temp;temp=min(temp,abs(v2c[i,j]))
   temp=float(np.finfo(float).max)
   for j in reversed(js):
    sign=total+int(v2c[i,j]<=0);c2v[i,j]=min(temp,c2v[i,j])*(1 if sign%2==0 else -1)*alpha
    if damping:c2v[i,j]=(1-damping)*c2v[i,j]+damping*old[i,j]
    temp=min(temp,abs(v2c[i,j]))
  last=[]
  for j,rs in enumerate(cols):
   temp=prior[j]
   for i in rs:v2c[i,j]=temp;temp+=c2v[i,j]
   last.append(temp)
  hard=np.array([x<=0 for x in last],dtype=np.uint8)
  if np.array_equal(d@hard%2,s):return np.array(last),it
  for j,rs in enumerate(cols):
   temp=0.
   for i in reversed(rs):v2c[i,j]+=temp;temp+=c2v[i,j]
 return np.array(last),iters

def test_parameterized_bp_and_reset():
 rng=np.random.default_rng(1102026)
 for trial in range(40):
  # Degree >=2 avoids degenerate infinite check messages in this finite-LLR contract.
  d=sparse.csr_matrix(rng.integers(0,2,(4,10)));d[:,:2]=1;p=rng.uniform(.01,.2,10);x=rng.integers(0,2,10,dtype=np.uint8);s=np.asarray(d@x%2,dtype=np.uint8)
  if not np.any(s):s=np.asarray(d@np.eye(10,dtype=np.uint8)[0]%2,dtype=np.uint8)
  for scale,damp,serial in [(.625,0,False),(.8,.25,False),(.5,0,False),(.8,0,True)]:
   o=LocalSolver(4,supports(d),p.tolist(),np.log((1-p)/p).tolist(),'bphuf',7,0);o.configure_bp(scale,damp,serial);ans=o.solve(s)
   if serial:
    ref=BpDecoder(d,error_channel=p.tolist(),max_iter=7,bp_method='minimum_sum',ms_scaling_factor=scale,schedule='serial',omp_thread_count=1);ref.decode(s);llr=np.asarray(ref.log_prob_ratios);iterations=ref.iter
   else:llr,iterations=ref_bp(d,p,s,scale,damp,7)
   assert np.array_equal(ans['llr'],llr),(scale,damp,serial,ans['llr'],llr)
   assert ans['counts']['bp_iterations']==iterations
   assert np.array_equal(d@ans['correction']%2,s)
   first=np.asarray(ans['correction']).copy();o.solve(np.zeros(4,dtype=np.uint8));assert np.array_equal(o.solve(s)['correction'],first)

def test_original_decoder_output_fidelity():
 for work in WORKS:
  a=model(work);item=json.loads((ROOT/'results/new_samples/manifest.json').read_text())['workloads'][work];ss=np.load(ROOT/item['splits']['validation']['path'])['detectors'][:16]
  for radius in [1,2]:
   obj=native(a,'repair'+str(radius));old=make(a,dict(kind='native',family='bphuf',policy='repair'+str(radius),persistent=True))
   expected=[]
   for s in ss:
    y,x=obj.decode(s);yr,xr=old.decode(s);assert np.array_equal(x,xr) and np.array_equal(y,yr);expected.append(x.copy())
   for i in reversed(range(len(ss))):assert np.array_equal(obj.decode(ss[i])[1],expected[i])
