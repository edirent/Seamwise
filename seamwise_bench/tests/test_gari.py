import ctypes
import numpy as np
from seamwise_bench.common import ROOT,load_model
from seamwise_bench.gari import GariAdapter

def test_augmented_model_and_official_c_binding():
    a=load_model('surface_d3_p0.003_B4');b=GariAdapter(a,dict(iterations=100,ensemble=1,seed=1,schedule=1))
    t=b.transformation
    lib=ctypes.CDLL(str(ROOT/'vendor/gari/my_decoders/hbplib_v2.so'))
    f=lib.ldpc_dec_msaa_quantum_serial_big_matrix_c
    pd=ctypes.POINTER(ctypes.c_double);pi=ctypes.POINTER(ctypes.c_int);pb=ctypes.POINTER(ctypes.c_int8)
    f.argtypes=[pd,ctypes.c_int,pi,ctypes.c_int,ctypes.c_int,pi,ctypes.c_int,ctypes.c_int,ctypes.c_double,pb,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,pb,pd]
    n=a['d'].shape[0];na=t['nx']+t['nz'];hc=t['hcols'];hr=t['hrows']
    raw=np.load(a['path']/'samples.npz')['detectors'][:8].astype(np.uint8)
    for s in raw:
        target=np.ones(n+na,dtype=np.int8);target[:n]=1-2*s[t['permutation']].astype(np.int8)
        x=np.zeros(hc.shape[0],dtype=np.int8);post=np.zeros(hc.shape[0],dtype=np.float64)
        f(t['llr'].ctypes.data_as(pd),100,hr.ctypes.data_as(pi),hr.shape[0],hr.shape[1],hc.ctypes.data_as(pi),hc.shape[0],hc.shape[1],.96875,target.ctypes.data_as(pb),1,n,t['mx'],1,0,x.ctypes.data_as(pb),post.ctypes.data_as(pd))
        expected=np.zeros(a['d'].shape[1],dtype=np.uint8);expected[t['marginal']]=x[:na]
        frame,correction=b.decode(s)
        assert np.array_equal(expected,correction)
        assert np.array_equal(a['l']@expected%2,frame)
