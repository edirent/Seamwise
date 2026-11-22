#!/usr/bin/env python3
"""Finite oracle-only investigation; never used in production decoding/timing."""
import sys,pathlib,itertools,random,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from seamwise_bench.common import ROOT,atomic
from algebra import State,apply

class CanonicalState(State):
    def __init__(self,target=0,priority=()):
        super().__init__(target);self.priority=priority;self.exchanges=0;self.witness_entries_examined=0
    def insert(self,column,j):
        v,c=column,1<<j
        for pivot in sorted(self.basis,reverse=True):
            if v>>pivot&1:
                b,w=self.basis[pivot];v^=b;c^=w
        self.inserted.add(j)
        if v:
            pivot=v.bit_length()-1;self.basis[pivot]=(v,c)
            if self.residual>>pivot&1:self.residual^=v;self.witness^=c
        else:
            self.relations.append(c)
            cycle=[k for k in range(len(self.priority)) if c>>k&1]
            worst=max(cycle,key=lambda k:(self.priority[k],k))
            if worst!=j:
                self.exchanges+=1
                for pivot,(b,w) in list(self.basis.items()):
                    self.witness_entries_examined+=1
                    if w>>worst&1:self.basis[pivot]=(b,w^c)
                if self.witness>>worst&1:self.witness^=c

def reference(cols,target,priority):
    s=State(target)
    for j in sorted(range(len(cols)),key=lambda j:(priority[j],j)):s.insert(cols[j],j)
    return s

def main():
    cases=0;naive_differences=0;exchange_count=0;examined=0
    for cols in itertools.product(range(4),repeat=3):
        for target in range(4):
            for order in itertools.permutations(range(3)):
                for priorities in itertools.permutations(range(3)):
                    a=CanonicalState(target,priorities);naive=State(target)
                    for j in order:a.insert(cols[j],j);naive.insert(cols[j],j)
                    r=reference(cols,target,priorities)
                    assert bool(a.residual)==bool(r.residual)
                    assert apply(cols,a.witness)^a.residual==target
                    if not r.residual:
                        assert a.witness==r.witness
                        naive_differences+=naive.witness!=r.witness
                    cases+=1;exchange_count+=a.exchanges;examined+=a.witness_entries_examined
    rng=random.Random(20261109)
    for trial in range(1000):
        n=rng.randint(1,10);m=rng.randint(1,16);cols=[rng.randrange(1<<n) for _ in range(m)];priorities=[rng.randrange(4) for _ in range(m)]
        target=apply(cols,rng.randrange(1<<m));order=list(range(m));rng.shuffle(order);a=CanonicalState(target,priorities);naive=State(target)
        for j in order:a.insert(cols[j],j);naive.insert(cols[j],j)
        r=reference(cols,target,priorities);assert not a.residual and a.witness==r.witness
        cases+=1;naive_differences+=naive.witness!=r.witness;exchange_count+=a.exchanges;examined+=a.witness_entries_examined
    result=dict(status='PASS',finite_systems=cases,naive_working_witness_differs_from_canonical=naive_differences,canonical_basis_exchanges=exchange_count,witness_rows_examined=examined,
                invariant='Maintain the unique minimum-(priority,id) linear-matroid basis. A dependent insertion exchanges the largest ordered fault in its fundamental cycle and substitutes that kernel relation in all witnesses. A consistent target then has the same unique correction on that basis as the frozen terminal policy.',
                production_status='NOT_IMPLEMENTED_NATIVE; current measured decoder retains terminal canonical reconstruction',
                scope='Correctness oracle investigation only, no latency/speed claim; sparse witness substitutions scan current pivots and can regress whole-path time. Native integration needs its own exact-output and timing ablation.')
    atomic(ROOT/'evidence/terminal_canonical_investigation.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
