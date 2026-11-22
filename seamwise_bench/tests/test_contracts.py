import itertools
import json
import numpy as np
import pytest
from scipy import sparse
from seamwise_bench.common import ROOT
from seamwise_bench.adapters import make
from seamwise_bench.analysis import paired,wilson

def model(columns,logical,n=2,p=None,labels=None,blocks=2):
    m=len(columns);q=max([i for v in logical for i in v],default=-1)+1
    d=sparse.csr_matrix(np.array([[i in v for v in columns] for i in range(n)],dtype=np.uint8))
    l=sparse.csr_matrix(np.array([[i in v for v in logical] for i in range(q)],dtype=np.uint8).reshape(q,m))
    return dict(d=d,l=l,p=np.array(p or [.1]*m),labels=np.array(labels or [i%blocks for i in range(n)]),meta=dict(blocks=blocks))

def test_invisible_duplicate_logical_and_order():
    # Duplicate detector supports with different observable tags are preserved;
    # an invisible logical mechanism with prior>.5 is committed centrally.
    a=model([[0],[0],[1],[]],[[0],[1],[],[1]],p=[.1,.1,.1,.8])
    configs=[dict(kind='native',family='huf',persistent=p,policy=pol) for p in [False,True] for pol in ['joint','cut','halo1','repair1']]
    for cfg in configs:
        b=make(a,cfg)
        for s in itertools.product(range(2),repeat=2):
            s=np.array(s,dtype=np.uint8);y,x=b.decode(s)
            assert np.array_equal(a['d']@x%2,s)
            assert x[3]==1 and np.array_equal(a['l']@x%2,y)
            if cfg['policy']=='joint':assert x[1]==0 # deterministic dependent free variable

def test_disconnected_and_inconsistent_local():
    a=model([[0],[1]],[[0],[]],n=3,labels=[0,1,1])
    b=make(a,dict(kind='native',family='huf',persistent=True,policy='repair1'),audit=True)
    out=b.backend.decode_audit(np.array([0,0,1],dtype=np.uint8))
    assert out['fallback'] and np.array_equal(out['correction'],[0,0])
    assert not np.array_equal(a['d']@out['correction']%2,[0,0,1])

def test_zero_and_all_zero_matrix():
    a=model([[],[]],[[],[]],n=2,labels=[0,1]);a['l']=sparse.csr_matrix((3,2),dtype=np.uint8)
    b=make(a,dict(kind='native',family='huf',persistent=True,policy='joint'))
    y,x=b.decode(np.zeros(2,dtype=np.uint8));assert y.shape==(3,) and not np.any(x) and not np.any(y)

def test_exhaustive_small_differential():
    for columns in itertools.product([[],[0],[1],[0,1]],repeat=3):
        a=model(list(columns),[[0],[],[0]])
        r=make(a,dict(kind='python',family='huf',persistent=False,policy='joint'))
        for persist in [False,True]:
            n=make(a,dict(kind='native',family='huf',persistent=persist,policy='joint',dense_terminal=True))
            for s in itertools.product(range(2),repeat=2):
                s=np.array(s,dtype=np.uint8)
                assert np.array_equal(r.decode(s)[1],n.decode(s)[1])

def test_tie_weights_and_bp_clipping():
    a=model([[0],[0,1],[1],[0]],[[0],[],[0],[1]],p=[.5-1e-12,.5,.5+1e-12,.1])
    for family in ['huf','bphuf']:
        for p in [False,True]:
            cfg=dict(kind='native',family=family,persistent=p,policy='joint')
            b=make(a,cfg);r=make(a,dict(cfg,kind='python'))
            for s in itertools.product(range(2),repeat=2):
                s=np.array(s,dtype=np.uint8);assert np.array_equal(b.decode(s)[1],r.decode(s)[1])

def test_adapter_native_lsd_matches_official():
    a=model([[0],[0,1],[1],[0]],[[0],[],[0],[1]])
    for family in ['lsd','osd']:
        b=make(a,dict(kind='native',family=family,policy='joint',order=0));r=make(a,dict(kind=family,order=0))
        for s in itertools.product(range(2),repeat=2):
            s=np.array(s,dtype=np.uint8);assert np.array_equal(b.decode(s)[1],r.decode(s)[1])

def test_pair_statistics_zero_and_discordance():
    r=paired([0,1,0,1],[0,0,1,1]);assert r['cells']==dict(both_correct=1,only_A_wrong=1,only_B_wrong=1,both_wrong=1)
    r=paired([0]*64,[0]*64);assert r['noninferiority']!='PASS' and r['noninferiority_one_sided_upper']>0
    lo,hi=wilson(0,64);assert lo>=0 and hi>0

def test_tesseract_capability_guard_and_metadata():
    from seamwise_bench.common import load_model,UnsupportedModel
    a=model([[0],[]],[[0],[1]],p=[.1,.8])
    with pytest.raises(UnsupportedModel):make(a,dict(kind='tesseract',det_beam=5,pqlimit=200000))
    b=make(load_model('surface_d3_p0.003_B4'),dict(kind='tesseract',det_beam=5,pqlimit=200000))
    assert json.dumps(b.resolved_config)
