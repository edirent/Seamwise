"""Explicit CSS Bell-reference circuits and exact circuit-derived DEM artifacts."""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
from scipy import sparse
import stim

def rref(a):
    a=np.array(a,dtype=np.uint8,copy=True)
    piv=[]; r=0
    for c in range(a.shape[1]):
        hits=np.flatnonzero(a[r:,c])
        if not len(hits): continue
        j=r+int(hits[0]); a[[r,j]]=a[[j,r]]
        for i in range(len(a)):
            if i!=r and a[i,c]: a[i]^=a[r]
        piv.append(c); r+=1
        if r==len(a): break
    return a[:r],piv

def rank(a): return len(rref(a)[1])

def nullspace(a):
    a=np.asarray(a,dtype=np.uint8); rr,piv=rref(a)
    free=[i for i in range(a.shape[1]) if i not in piv]
    out=np.zeros((len(free),a.shape[1]),dtype=np.uint8)
    for t,c in enumerate(free):
        out[t,c]=1
        for j,p in enumerate(piv): out[t,p]=rr[j,c]
    return out

def inverse(a):
    n=len(a); aug=np.concatenate([a,np.eye(n,dtype=np.uint8)],axis=1)
    rr,piv=rref(aug)
    if piv[:n]!=list(range(n)): raise ValueError('Singular pairing')
    return rr[:,n:]

def quotient(ker,stabs):
    # Incrementally reduce integer-encoded row vectors.
    basis={}; selected=[]
    def add(row):
        v=int.from_bytes(np.packbits(row,bitorder='little').tobytes(),'little')
        while v:
            p=v.bit_length()-1
            if p in basis: v^=basis[p]
            else: basis[p]=v; return True
        return False
    for row in stabs: add(row)
    for row in ker:
        if add(row): selected.append(row)
    return np.array(selected,dtype=np.uint8)

def logicals(hx,hz):
    assert not np.any(hx@hz.T%2)
    lx=quotient(nullspace(hz),hx)
    lz=quotient(nullspace(hx),hz)
    pair=lx@lz.T%2
    lz=inverse(pair).T@lz%2
    assert np.array_equal(lx@lz.T%2,np.eye(len(lx),dtype=np.uint8))
    return lx,lz

def surface_spec(d):
    c=stim.Circuit.generated('surface_code:rotated_memory_z',distance=d,rounds=1)
    instructions=list(c.flattened())
    data=next([t.value for t in ins.targets_copy()] for ins in reversed(instructions)
              if ins.name=='M')
    anc=next([t.value for t in ins.targets_copy()] for ins in instructions if ins.name=='MR')
    data=sorted(data); anc=sorted(anc)
    di={q:i for i,q in enumerate(data)}; ai={q:i for i,q in enumerate(anc)}
    xanc=set(); layers=[]
    for ins in instructions:
        if ins.name=='MR': break
        if ins.name=='H': xanc.update(t.value for t in ins.targets_copy())
        if ins.name=='CX': layers.append([t.value for t in ins.targets_copy()])
    h=np.zeros((len(anc),len(data)),dtype=np.uint8)
    local_layers=[]
    for layer in layers:
        converted=[]
        for a,b in zip(layer[::2],layer[1::2]):
            ancq=a if a in ai else b; datq=b if a in ai else a
            h[ai[ancq],di[datq]]=1
            converted.extend([di[a] if a in di else len(data)+ai[a],
                              di[b] if b in di else len(data)+ai[b]])
        local_layers.append(converted)
    types=np.array([q in xanc for q in anc],dtype=bool)
    hx=h[types]; hz=h[~types]
    lx,lz=logicals(hx,hz)
    return dict(n=len(data),k=1,h=h,types=types,hx=hx,hz=hz,lx=lx,lz=lz,
                layers=local_layers,xanc=np.flatnonzero(types).tolist())

def bb_spec(n):
    ell,m={72:(6,6),144:(12,6)}[n]
    x=np.kron(np.roll(np.eye(ell,dtype=np.uint8),1,axis=1),np.eye(m,dtype=np.uint8))
    y=np.kron(np.eye(ell,dtype=np.uint8),np.roll(np.eye(m,dtype=np.uint8),1,axis=1))
    a=(np.linalg.matrix_power(x,3)+y+y@y)%2
    b=(np.linalg.matrix_power(y,3)+x+x@x)%2
    hx=np.concatenate([a,b],axis=1); hz=np.concatenate([b.T,a.T],axis=1)
    lx,lz=logicals(hx,hz)
    assert len(lx)==12
    return dict(n=n,k=12,h=np.concatenate([hx,hz]),
                types=np.array([True]*len(hx)+[False]*len(hz)),
                hx=hx,hz=hz,lx=lx,lz=lz,layers=[],xanc=[])

def pauli(n,row,kind,ref=None):
    ps=stim.PauliString(n)
    for i in np.flatnonzero(row): ps[int(i)]=kind
    if ref is not None: ps[ref]=kind
    return ps

def append_mapped(c,local,mapping):
    for ins in local:
        c.append(ins.name,[mapping[t.value] for t in ins.targets_copy()],ins.gate_args_copy())

def mpp_targets(support,kind):
    out=[]
    for i,q in enumerate(support):
        if i: out.append(stim.target_combiner())
        out.append(stim.target_x(int(q)) if kind=='X' else stim.target_z(int(q)))
    return out

def gate_pairs(b,t):
    pairs=[(i,i+1) for i in range(t%2,b-1,2)]
    return [(v,u) for u,v in pairs] if (t//2)%2 else pairs

def build_circuit(config):
    family=config['family']; b=config['blocks']; rounds=config['rounds']; p=config['p']
    spec=surface_spec(config['distance']) if family=='surface' else bb_spec(config['n'])
    n,k=spec['n'],spec['k']; h=spec['h']; nc=len(h)
    stride=n+k+(nc if family=='surface' else 0)
    c=stim.Circuit()
    stabs=[pauli(n+k,row,'X') for row in rref(spec['hx'])[0]]
    stabs +=[pauli(n+k,row,'Z') for row in rref(spec['hz'])[0]]
    for j in range(k):
        stabs +=[pauli(n+k,spec['lx'][j],'X',n+j),pauli(n+k,spec['lz'][j],'Z',n+j)]
    tab=stim.Tableau.from_stabilizers(stabs)
    init=tab.to_circuit('elimination')
    for block in range(b): append_mapped(c,init,{i:block*stride+i for i in range(n+k)})
    history=[[set() for _ in range(nc)] for _ in range(b)]
    # 2Bk commuting Bell stabilizers, tracked under the logical CNOT circuit.
    xlog=np.zeros((2*b*k,b*k),dtype=np.uint8); zlog=np.zeros_like(xlog)
    for i in range(b*k): xlog[2*i,i]=1; zlog[2*i+1,i]=1
    labels=[]; gates=[]
    for t in range(rounds+1):
        noisy=t<rounds
        if noisy:
            for u,v in gate_pairs(b,t):
                targets=[q for j in range(n) for q in (u*stride+j,v*stride+j)]
                c.append('CX',targets)
                if family=='surface': c.append('DEPOLARIZE2',targets,p)
                for check,isx in enumerate(spec['types']):
                    if isx: history[u][check]=history[u][check]^history[v][check]
                    else: history[v][check]=history[v][check]^history[u][check]
                for j in range(k):
                    xlog[:,v*k+j]^=xlog[:,u*k+j]
                    zlog[:,u*k+j]^=zlog[:,v*k+j]
                gates.append([t,u,v])
            if family=='bb':
                # Both sectors are sampled in the same Bell-reference circuit.
                c.append('DEPOLARIZE1',[block*stride+j for block in range(b) for j in range(n)],p)
        for block in range(b):
            base=block*stride
            if family=='surface':
                ancs=[base+n+k+j for j in range(nc)]
                xa=[ancs[j] for j in spec['xanc']]
                c.append('R',ancs)
                if noisy: c.append('X_ERROR',ancs,p)
                c.append('H',xa)
                if noisy: c.append('DEPOLARIZE1',xa,p)
                for layer in spec['layers']:
                    mapped=[base+q if q<n else base+n+k+q-n for q in layer]
                    c.append('CX',mapped)
                    if noisy: c.append('DEPOLARIZE2',mapped,p)
                c.append('H',xa)
                if noisy: c.append('DEPOLARIZE1',xa,p)
                start=c.num_measurements
                c.append('M',ancs,p if noisy else 0)
                measurements=list(range(start,start+nc))
            else:
                measurements=[]
                for j,row in enumerate(h):
                    targets=mpp_targets(base+np.flatnonzero(row),'X' if spec['types'][j] else 'Z')
                    measurements.append(c.num_measurements)
                    c.append('MPP',targets,p if noisy else 0)
            now=c.num_measurements
            for j,measurement in enumerate(measurements):
                ids=sorted(history[block][j]^{measurement})
                c.append('DETECTOR',[stim.target_rec(v-now) for v in ids],[block,j,t])
                labels.append(block)
                history[block][j]={measurement}
        c.append('TICK')
    for obs in range(2*b*k):
        pieces=[]
        kind='X' if obs%2==0 else 'Z'
        support=[]
        lm=xlog[obs] if kind=='X' else zlog[obs]
        basis=spec['lx'] if kind=='X' else spec['lz']
        for block in range(b):
            row=np.zeros(n,dtype=np.uint8)
            for j in range(k):
                if lm[block*k+j]: row^=basis[j]
            support.extend((block*stride+np.flatnonzero(row)).tolist())
        original=obs//2; ref=(original//k)*stride+n+original%k
        support.append(ref)
        c.append('MPP',mpp_targets(support,kind))
        c.append('OBSERVABLE_INCLUDE',[stim.target_rec(-1)],obs)
    dem=c.detector_error_model(decompose_errors=False,approximate_disjoint_errors=False).flattened()
    rows=[]; cols=[]; lr=[]; lc=[]; probs=[]
    for ins in dem:
        if ins.type!='error': continue
        j=len(probs); probs.append(ins.args_copy()[0]); detset=set(); logset=set()
        for target in ins.targets_copy():
            if target.is_relative_detector_id():
                v=target.val
                if v in detset: detset.remove(v)
                else: detset.add(v)
            elif target.is_logical_observable_id():
                v=target.val
                if v in logset: logset.remove(v)
                else: logset.add(v)
        for i in detset: rows.append(i);cols.append(j)
        for i in logset: lr.append(i);lc.append(j)
    d=sparse.csr_matrix((np.ones(len(rows),dtype=np.uint8),(rows,cols)),shape=(c.num_detectors,len(probs)))
    l=sparse.csr_matrix((np.ones(len(lr),dtype=np.uint8),(lr,lc)),shape=(c.num_observables,len(probs)))
    # Noiseless deterministic observables checked by exact DEM conversion above;
    # an explicit sampler check catches accidental initialization errors as well.
    return c,dem,d,l,np.array(probs),np.array(labels,dtype=np.int16),spec,gates

def save_model(path,config,shots,seed):
    path=Path(path);path.mkdir(parents=True,exist_ok=True)
    c,dem,d,l,p,labels,spec,gates=build_circuit(config)
    (path/'circuit.stim').write_text(str(c)+'\n')
    (path/'detector_model.dem').write_text(str(dem)+'\n')
    sparse.save_npz(path/'D.npz',d);sparse.save_npz(path/'L.npz',l)
    np.savez_compressed(path/'code.npz',HX=spec['hx'],HZ=spec['hz'],LX=spec['lx'],LZ=spec['lz'])
    np.savez_compressed(path/'metadata_arrays.npz',p=p,detector_blocks=labels)
    det,obs,err=dem.compile_sampler(seed=seed).sample(shots=shots,return_errors=True)
    assert np.array_equal((d@err.T).T%2,det)
    assert np.array_equal((l@err.T).T%2,obs)
    np.savez_compressed(path/'samples.npz',detectors=det,observables=obs,errors=err)
    meta=dict(config,shots=shots,seed=seed,detectors=d.shape[0],faults=d.shape[1],
              observables=l.shape[0],qubits=c.num_qubits,logical_cnots=gates,
              dem_options=dict(decompose_errors=False,approximate_disjoint_errors=False),
              extraction='scheduled ancilla circuit' if config['family']=='surface' else 'ideal commuting MPP with readout flips')
    (path/'model.json').write_text(json.dumps(meta,indent=2)+'\n')
    return meta
