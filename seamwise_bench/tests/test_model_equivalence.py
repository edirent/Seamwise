"""Model semantics, independent of any decoder's accuracy or growth policy."""
import numpy as np
import stim
from scipy import sparse

def test_separator_is_one_correlated_mechanism_and_logical_identity_retained():
    dem=stim.DetectorErrorModel('''
        error(0.03) D0 ^ D1 L0
        error(0.07) L1
        error(0.02) D0 L0
        error(0.04) D0 L1
    ''')
    # Explicit expected matrices: invisible logical fault, equal D supports with
    # distinct L tags, and a separated but JOINT first mechanism.
    d=sparse.csr_matrix(np.array([[1,0,1,1],[1,0,0,0]],dtype=np.uint8))
    l=sparse.csr_matrix(np.array([[1,0,1,0],[0,1,0,1]],dtype=np.uint8))
    det,obs,errors=dem.compile_sampler(seed=20261109).sample(shots=1000,return_errors=True)
    assert errors.shape[1]==4
    assert np.array_equal((d@errors.T).T%2,det)
    assert np.array_equal((l@errors.T).T%2,obs)
    assert np.any(errors[:,1])
