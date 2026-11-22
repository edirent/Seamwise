"""Explicit BP-assisted RESIDUAL-HUF variant, not the original HUF binary.
Common BP output, hard-decision residual, absolute-posterior edge costs,
and posterior-cost terminal column order are shared between oracle modes.
"""
import numpy as np
from ldpc import BpDecoder
from huf import HUF
from algebra import State

class BPHUF(HUF):
    def __init__(self,a,p,persistent):
        super().__init__(a,p,persistent)
        self.bp=BpDecoder(a,error_channel=np.asarray(p).tolist(),max_iter=30,bp_method='minimum_sum',ms_scaling_factor=.625,schedule='parallel',omp_thread_count=1)
        self.priority=np.log((1-p)/p)
    def fresh(self,faults,target):
        state=State(target)
        for j in sorted(faults,key=lambda j:(self.priority[j],j)):state.insert(self.columns[j],j)
        return state
    def decode(self,s):
        x=self.bp.decode(s).copy().astype(np.uint8)
        if self.bp.converge:
            self.stats.append(dict(peak_cluster=0,merge_sizes=[],unions=0,activations=0,bp_converged=True))
            return x
        llr=np.clip(np.asarray(self.bp.log_prob_ratios),-100,100)
        base=(llr<0).astype(np.uint8)
        target=(s+(self.a@base)%2)%2
        self.priority=np.abs(llr)
        self.weights=[max(1e-9,float(self.priority[f-self.n])) for _,f in self.edges]
        y=super().decode(target.astype(np.uint8))
        return y^base
