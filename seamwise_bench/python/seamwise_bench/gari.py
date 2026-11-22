"""Verified full-joint GARI graph adapter. Preparation only is Python."""
import numpy as np
from scipy import sparse
from .adapters import supports
from .common import UnsupportedModel

def transformation(model):
    import models
    meta=model['meta']
    spec=models.surface_spec(meta['distance']) if meta['family']=='surface' else models.bb_spec(meta['n'])
    d=model['d'].tocsc();l=model['l'].tocsc();n,m=d.shape
    kinds=spec['types'];xrows=[i for i in range(n) if kinds[i%len(kinds)]];zrows=[i for i in range(n) if not kinds[i%len(kinds)]]
    permutation=np.array(xrows+zrows,dtype=np.int32);inverse=np.argsort(permutation);xset=set(xrows)
    dx={};dz={};joint=[];log=supports(l);original=supports(d)
    for j,col in enumerate(original):
        x=tuple(i for i in col if i in xset);z=tuple(i for i in col if i not in xset)
        if x and z:joint.append((j,x,z))
        elif x:
            if x in dx:raise UnsupportedModel('GARI ambiguous X support with separate fault identity')
            dx[x]=j
        elif z:
            if z in dz:raise UnsupportedModel('GARI ambiguous Z support with separate fault identity')
            dz[z]=j
        else:raise UnsupportedModel('GARI invisible fault map not supported')
    xfaults=list(dx.values());zfaults=list(dz.values());marginal=xfaults+zfaults;nx=len(xfaults);nz=len(zfaults);na=nx+nz
    lookup={j:k for k,j in enumerate(marginal)}
    # Binary column identities establish BOTH syndrome and observable maps for
    # every original fault, including different logical tags if encountered.
    for j,x,z in joint:
        if x not in dx or z not in dz:raise UnsupportedModel('GARI projection missing')
        if set(original[j])!=set(original[dx[x]])^set(original[dz[z]]):raise ValueError('GARI detector map')
        if set(log[j])!=set(log[dx[x]])^set(log[dz[z]]):raise UnsupportedModel('GARI logical map not representable by supplied projection')
    # First na variables are X/Z marginals, followed by the original faults in
    # X-only, Z-only, joint order. Auxiliary parity checks fix marginals.
    rr=[];cc=[]
    for k,j in enumerate(marginal):
        for i in original[j]:rr.append(int(inverse[i]));cc.append(k)
        rr.extend([n+k,n+k]);cc.extend([k,na+k])
    for k,(j,x,z) in enumerate(joint):
        rr.extend([n+lookup[dx[x]],n+lookup[dz[z]]]);cc.extend([2*na+k,2*na+k])
    aug=sparse.csr_matrix((np.ones(len(rr),dtype=np.uint8),(rr,cc)),shape=(n+na,na+m))
    reordered=marginal+[j for j,_,_ in joint]
    priors=np.concatenate([np.full(na,.5),model['p'][reordered]])
    # Exact independent-mechanism XOR marginals are used only for ensemble
    # selection; original fault priors in the augmented model are unchanged.
    products=np.ones(na)
    for k,j in enumerate(marginal):products[k]*=1-2*model['p'][j]
    for j,x,z in joint:
        products[lookup[dx[x]]]*=1-2*model['p'][j];products[lookup[dz[z]]]*=1-2*model['p'][j]
    pm=(1-products)/2;score=np.log((1-pm)/pm)
    def padded(matrix):
        a=matrix.tocsr();deg=np.diff(a.indptr);out=np.zeros((a.shape[0],max(1,int(deg.max(initial=0)))),dtype=np.int32)
        for i in range(a.shape[0]):out[i,:deg[i]]=a.indices[a.indptr[i]:a.indptr[i+1]]+1
        return out
    # Verify the unique augmentation of seeded original faults. This is
    # preparation, separate from sampled circuit outcomes and decoder timing.
    rng=np.random.default_rng(2026110907);trials=rng.integers(2,size=(16,m),dtype=np.uint8)
    for e in trials:
        marg=np.zeros(na,dtype=np.uint8)
        for k,j in enumerate(marginal):marg[k]=e[j]
        for j,x,z in joint:marg[lookup[dx[x]]]^=e[j];marg[lookup[dz[z]]]^=e[j]
        y=np.concatenate([marg,e[reordered]]);target=np.concatenate([np.asarray(d@e%2)[permutation],np.zeros(na,dtype=np.uint8)])
        assert np.array_equal(aug@y%2,target)
        projected=np.zeros(m,dtype=np.uint8);projected[marginal]=marg
        assert np.array_equal(l@e%2,l@projected%2)
    return dict(hrows=padded(aug),hcols=padded(aug.T),llr=np.log((1-priors)/priors),score=score,
                permutation=permutation,marginal=marginal,nx=nx,nz=nz,mx=len(xrows),reordered=reordered,augmented=aug,
                proof='column-wise D and L identities; unique aux extension; original priors unchanged, auxiliary priors 0.5')

class GariAdapter:
    validity='CORRECTION_AUDITED_EXTERNALLY'
    def __init__(self,model,cfg,audit=False):
        import _gari
        t=transformation(model);self.transformation=t
        self.backend=_gari.Gari(t['hrows'],t['hcols'],t['llr'].tolist(),t['score'].tolist(),t['permutation'].tolist(),t['marginal'],
                              supports(model['d']),supports(model['l']),model['l'].shape[0],t['mx'],t['nx'],t['nz'],cfg.get('iterations',100),cfg.get('ensemble',1),cfg.get('seed',1),cfg.get('schedule',1),cfg.get('scale',.96875))
        self.backend.two_sector=cfg.get('stopping','full')=='two_sector'
    def decode(self,s):return self.backend.decode(s)
