"""Offline partition/repair reference implementation; every output is checked."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy import sparse
from ldpc import BeliefFindDecoder, BpLsdDecoder, BpOsdDecoder

COMMON=dict(max_iter=30,bp_method='minimum_sum',ms_scaling_factor=.625,
            schedule='parallel',omp_thread_count=1)
ENGINE_OPTIONS={
    'BF':dict(uf_method='inversion',bits_per_step=1),
    'LSD0':dict(lsd_method='LSD_0',lsd_order=0),
    'LSD2':dict(lsd_method='LSD_CS',lsd_order=2),
    'OSD0':dict(osd_method='OSD_0',osd_order=0),
    'OSD2':dict(osd_method='OSD_CS',osd_order=2),
}

def make_solver(d,p,engine):
    cls=BeliefFindDecoder if engine=='BF' else BpOsdDecoder if engine.startswith('OSD') else BpLsdDecoder
    return cls(d,error_channel=np.asarray(p).tolist(),**COMMON,**ENGINE_OPTIONS[engine])

def logical_freedom(d,l):
    basis={}
    def add_sparse(matrix):
        added=0
        matrix=matrix.tocsr()
        for i in range(matrix.shape[0]):
            v=0
            for j in matrix.indices[matrix.indptr[i]:matrix.indptr[i+1]]:
                v^=1<<int(j)
            while v:
                pivot=v.bit_length()-1
                if pivot in basis: v^=basis[pivot]
                else: basis[pivot]=v;added+=1;break
        return added
    rd=add_sparse(d);rho=add_sparse(l)
    return rd,rho

@dataclass
class Window:
    columns: np.ndarray
    rows: np.ndarray
    matrix: object
    rho: int|None=None
    detector_rank: int|None=None

class Stack:
    def __init__(self,d,l,p,labels,blocks,engine,core=2):
        self.d=d.tocsr();self.l=l.tocsr();self.p=p;self.labels=labels
        self.blocks=blocks;self.engine=engine;self.core=core
        self.weights=np.log((1-p)/p)
        self.owner=np.full(d.shape[1],blocks,dtype=np.int16)
        coo=d.tocoo()
        np.minimum.at(self.owner,coo.col,labels[coo.row])
        self.solvers={};self.windows={};self.cutplans={};self.bands={}
        self.global_solver=make_solver(d,p,engine)
        self.zero_columns=np.flatnonzero(self.owner==blocks)
        self.zero_estimate=np.zeros(d.shape[1],dtype=np.uint8)
        self.zero_estimate[self.zero_columns]=(p[self.zero_columns]>.5)

    def solver(self,window):
        key=(window.columns.tobytes(),window.rows.tobytes())
        if key not in self.solvers:
            self.solvers[key]=make_solver(window.matrix,self.p[window.columns],self.engine)
        return self.solvers[key]

    def prepare_cut(self,halo):
        if halo in self.cutplans:return self.cutplans[halo]
        plans=[]
        for start in range(0,self.blocks,self.core):
            end=min(self.blocks,start+self.core+halo)
            cols=np.flatnonzero((self.owner>=start)&(self.owner<end))
            touched=np.flatnonzero(np.asarray(self.d[:,cols].getnnz(axis=1)).ravel())
            # Condition on committed columns and include exactly touched rows
            # with no remaining outside-window columns. Frontier-open rows
            # are excluded; core rows are always included by ownership.
            outside=np.flatnonzero((self.owner>=end)&(self.owner<self.blocks))
            external_count=np.asarray(self.d[:,outside].getnnz(axis=1)).ravel()
            rows=touched[external_count[touched]==0]
            rows=np.union1d(rows,np.flatnonzero((self.labels>=start)&
                               (self.labels<min(start+self.core,self.blocks))))
            win=Window(cols,rows,self.d[rows][:,cols].tocsr())
            commit=(self.owner[cols]<min(start+self.core,self.blocks))
            core_rows=np.flatnonzero((self.labels>=start)&
                                    (self.labels<min(start+self.core,self.blocks)))
            if len(cols):self.solver(win)
            plans.append((win,commit,core_rows))
        self.cutplans[halo]=plans;return plans

    def prepare_repair(self,radius):
        if radius in self.bands:return self.bands[radius]
        bands=[]
        for seam in range(self.core,self.blocks,self.core):
            cols=np.flatnonzero((self.owner>=max(0,seam-radius))&
                               (self.owner<min(self.blocks,seam+radius)))
            rows=np.flatnonzero(np.asarray(self.d[:,cols].getnnz(axis=1)).ravel())
            win=Window(cols,rows,self.d[rows][:,cols].tocsr())
            win.detector_rank,win.rho=logical_freedom(win.matrix,self.l[:,cols])
            if len(cols):self.solver(win)
            bands.append((seam,win))
        self.bands[radius]=bands;return bands

    def prepare(self,policies):
        for policy in policies:
            if policy.startswith('halo'):self.prepare_cut(int(policy[-1]))
            elif policy=='cut':self.prepare_cut(0)
            elif policy.startswith('repair') or policy=='rank1':
                self.prepare_cut(0)
                self.prepare_repair(1 if policy=='rank1' else int(policy[-1]))

    def global_decode(self,s):
        x=self.global_solver.decode(s).copy().astype(np.uint8)
        x[self.zero_columns]=self.zero_estimate[self.zero_columns]
        return x

    def cut(self,s,halo):
        x=self.zero_estimate.copy();res=s.copy();fallback=False
        for win,commit,core_rows in self.prepare_cut(halo):
            if not len(win.columns):
                if np.any(res[core_rows]):fallback=True;break
                continue
            z=self.solver(win).decode(res[win.rows]).copy().astype(np.uint8)
            if not np.array_equal(win.matrix@z%2,res[win.rows]):fallback=True;break
            cols=win.columns[commit];value=z[commit]
            x[cols]=value;res^=(self.d[:,cols]@value%2).astype(np.uint8)
            if np.any(res[core_rows]):fallback=True;break
        if fallback or np.any(res):
            return self.global_decode(s),True
        return x,False

    def decode(self,s,policy):
        if policy=='joint':return self.global_decode(s),False,[]
        if policy=='cut' or policy.startswith('halo'):
            x,fb=self.cut(s,0 if policy=='cut' else int(policy[-1]))
            return x,fb,[]
        radius=1 if policy=='rank1' else int(policy[-1])
        x,fb=self.cut(s,0);events=[]
        if not np.array_equal(self.d@x%2,s):return x,fb,events
        for seam,win in self.prepare_repair(radius):
            before=(self.l@x%2).astype(np.uint8)
            old=x[win.columns].copy();oldcost=float(self.weights[win.columns]@old)
            event=dict(seam=seam,radius=radius,rho=win.rho,accepted=False,
                       skipped=False,consistent=True,cost_drop=0.,
                       before=before,after=before)
            if policy=='rank1' and win.rho==0:
                event['skipped']=True;events.append(event);continue
            # The incumbent satisfies Dx=s, so conditioning the exterior is
            # exactly equivalent to D_J x_J as the local target.
            target=(win.matrix@old%2).astype(np.uint8)
            z=self.solver(win).decode(target).copy().astype(np.uint8)
            valid=np.array_equal(win.matrix@z%2,target)
            event['consistent']=valid
            newcost=float(self.weights[win.columns]@z)
            if valid and newcost<oldcost-1e-10:
                x[win.columns]=z;event['accepted']=True
                event['cost_drop']=oldcost-newcost
                event['after']=(self.l@x%2).astype(np.uint8)
            events.append(event)
        return x,fb,events

def method_grid():
    # Crossed policies for every engine, plus BF width/radius ablations.
    grid=[(engine,policy) for engine in ['BF','LSD0','LSD2','OSD0']
          for policy in ['joint','cut','repair1']]
    grid += [('BF','halo1'),('BF','halo2'),('BF','repair2'),('BF','rank1')]
    return grid
