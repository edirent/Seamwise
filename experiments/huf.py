"""Rebuilt and persistent exact-oracle HUF reference backends.

Weighted boundary clocks; select smallest unsatisfied component. This is a
new Python reference implementation, not the authors' original HUF binary.
Both modes use the SAME scheduling, activation and terminal solution policy.
Bitsets are prototypes, not the support-local cost-model implementation.
"""
import heapq
import numpy as np
from algebra import State


class HUF:
    def __init__(self, matrix, probabilities, persistent):
        self.a=matrix.tocsc();self.n,self.m=self.a.shape
        self.neighbors=[list(map(int,self.a.indices[self.a.indptr[j]:self.a.indptr[j+1]])) for j in range(self.m)]
        self.columns=[sum(1<<i for i in ns) for ns in self.neighbors]
        self.edges=[(i,self.n+j) for j,ns in enumerate(self.neighbors) for i in ns]
        self.inc=[[] for _ in range(self.n+self.m)]
        weights=[]
        for e,(i,f) in enumerate(self.edges):
            self.inc[i].append(e);self.inc[f].append(e)
            weights.append(max(1e-9,float(np.log((1-probabilities[f-self.n])/probabilities[f-self.n]))))
        self.weights=weights;self.persistent=persistent
        self.stats=[]

    def fresh(self, faults, target):
        s=State(target)
        for j in sorted(faults):s.insert(self.columns[j],j)
        return s

    def decode(self, syndrome):
        try:return self._decode(syndrome)
        except ValueError as e:
            if str(e)=='inconsistent component':return np.zeros(self.m,dtype=np.uint8)
            raise

    def _decode(self, syndrome):
        n,m=self.n,self.m;v=n+m
        parent=list(range(v));members={i:[i] for i in range(v)}
        states={i:State(int(syndrome[i])<<i if i<n else 0) for i in range(v)}
        for i in range(n):states[i].checks={i}
        for j in range(m):states[n+j].faults={j}
        def root(i):
            while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
            return i
        target=sum(int(t)<<i for i,t in enumerate(syndrome))
        def eligible(st):
            return {j for j in st.faults if all(root(i)==root(n+j) for i in self.neighbors[j])}
        heap=[(1,i) for i in range(n) if syndrome[i]];heapq.heapify(heap)
        clocks=self.weights.copy();sizes=[];unions=0;activations=0
        while heap:
            size,r=heapq.heappop(heap)
            if r not in states or len(members[r])!=size or not states[r].residual:continue
            boundary=sorted({e for u in members[r] for e in self.inc[u] if root(self.edges[e][0])!=root(self.edges[e][1])})
            if not boundary:raise ValueError('inconsistent component')
            delta=min(clocks[e] for e in boundary)
            sat=[]
            for e in boundary:
                clocks[e]-=delta
                if clocks[e]<=1e-8:sat.append(e)
            for e in sat:
                a,b=map(root,self.edges[e])
                if a==b:continue
                if a>b:a,b=b,a
                states[a]=State.merge(states[a],states.pop(b));parent[b]=a
                members[a]+=members.pop(b);s=states[a]
                new=eligible(s)-s.inserted
                if self.persistent:
                    for j in sorted(new):s.insert(self.columns[j],j);activations+=1
                # Rebuilding uses the same eligibility state; residual query
                # is reconstructed only once per completed growth event.
                else:s.inserted|=new
                unions+=1;sizes.append(len(members[a]));r=a
            r=root(r)
            if not self.persistent:
                s=states[r];temp=self.fresh(s.inserted,target & sum(1<<i for i in s.checks))
                s.basis=temp.basis;s.residual=temp.residual;s.witness=temp.witness
            if states[r].residual:heapq.heappush(heap,(len(members[r]),r))
        # Fixed deterministic terminal solve in BOTH modes isolates the
        # effect of oracle persistence and guarantees identical corrections.
        out=0
        for s in states.values():
            if s.inserted:
                terminal=self.fresh(s.inserted,target & sum(1<<i for i in s.checks))
                if terminal.residual:raise ValueError('invalid terminal')
                out^=terminal.witness
        x=np.fromiter(((out>>j)&1 for j in range(m)),dtype=np.uint8,count=m)
        if not np.array_equal(self.a@x%2,syndrome):raise ValueError('invalid global correction')
        self.stats.append(dict(peak_cluster=max(sizes,default=1),merge_sizes=sizes,unions=unions,activations=activations))
        return x
