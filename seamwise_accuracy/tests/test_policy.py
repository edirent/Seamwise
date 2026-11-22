import sys,pathlib,math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from runner import factory
import _accuracy_native

def toy(selection='cost',adaptive=False):
 weights=[1.5,2.,2.,2.];p=[1/(1+math.exp(w)) for w in weights]
 obj=_accuracy_native.AccuracyDecoder(1,[[0]]*4,[[],[0],[0],[0]],p,weights,[0],4,dict(family='huf',band_family='huf',radius=2,K=4,depth=1,selection=selection,adaptive=adaptive,audit=True),{2:[[[0,1],[0,2],[0,3]]]});obj.observable_count=1;return obj

def test_class_mass_distinct_configurations_and_nonmonotonic_label():
 cost=toy('cost');mass=toy('class_mass');s=np.array([1],dtype=np.uint8)
 ya,xa=cost.decode(s);yb,xb=mass.decode(s);assert xa.tolist()==[1,0,0,0] and ya.tolist()==[0];assert sum(xb)==1 and xb[0]==0 and yb.tolist()==[1]
 assert cost.stats()['higher_cost_updates']==0 and mass.stats()['higher_cost_updates']==1
 ev=mass.events()[0];assert len(ev['candidates'])==4 and ev['classes']==2 and ev['generated_rank']==1
 # Three DIFFERENT configurations share the higher-minimum-cost class.
 assert sum(c['logical_signature'][0]==1 for c in ev['candidates'])==3
 for obj in [cost,mass]:
  previous=obj.decode(s)[1].copy();obj.decode(np.array([0],dtype=np.uint8));assert np.array_equal(obj.decode(s)[1],previous)

def test_adaptive_empty_band_and_kernel_guard():
 obj=toy('class_mass',True);obj.decode(np.array([1],dtype=np.uint8));assert obj.stats()['escalations']==1 and obj.stats()['repair_solver_calls']<=2
 for s in [np.array([],dtype=np.uint8),np.array([2],dtype=np.uint8)]:
  try:obj.decode(s)
  except ValueError:pass
  else:raise AssertionError('invalid syndrome accepted')
 try:_accuracy_native.AccuracyDecoder(1,[[0]],[[0]],[.1],[2.],[0],4,dict(radius=2,K=2),{2:[[[0]]]})
 except ValueError:pass
 else:raise AssertionError('invalid detector-kernel move accepted')

def test_K1_exact_and_native_variants_reset():
 data=json.loads((ROOT/'results/new_samples/manifest.json').read_text())['workloads']
 for work in WORKS:
  a=model(work);ss=np.load(ROOT/data[work]['splits']['validation']['path'])['detectors'][:12];radius=2 if work.startswith('bb') else 1
  baseline=make(a,dict(kind='native',family='bphuf',persistent=True,policy='repair'+str(radius)))
  cfg=dict(name='K1',kind='new',candidate=True,K=1,radius=radius,policy='repair'+str(radius),selection='cost');obj=factory(a,cfg)
  for s in ss:assert np.array_equal(obj.decode(s)[1],baseline.decode(s)[1])
  for selection in ['cost','class_mass']:
   cfg.update(K=4,selection=selection,adaptive=True,scale=.8,damping=.25,iterations=60);obj=factory(a,cfg,audit=True);expected=[]
   for s in ss:
    y,x=obj.decode(s);assert valid(a,x,s) and np.array_equal(frame(a,x),y);expected.append(x.copy());assert obj.stats()['repair_solver_calls']<=2
    for ev in obj.events():
     assert len(ev['candidates'])<=5
     if selection=='cost':assert ev['newcost']<=ev['oldcost']+1e-10
   for i in np.random.default_rng(71).permutation(len(ss)):assert np.array_equal(obj.decode(ss[i])[1],expected[i])
  cfg.update(joint=True,adaptive=False,selection='cost');joint=factory(a,cfg)
  for s in ss[:4]:
   y,x=joint.decode(s);assert valid(a,x,s) and np.array_equal(frame(a,x),y);assert joint.stats()['repair_solver_calls']==0
