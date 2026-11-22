#!/usr/bin/env python3
"""Validation-only point Pareto envelopes and prespecified mean-latency budgets."""
import sys,pathlib,json,collections
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from seamwise_bench.common import ROOT,atomic
from seamwise_bench.analysis import analyze

def main():
    index=json.loads((ROOT/'evidence/run_index.json').read_text())
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    path=ROOT/index['validation'];a=analyze(path);groups=collections.defaultdict(list)
    for r in a['summary']:
        if r['service_failures']==0:groups[r['workload']].append(r)
    results=[]
    for work,rows in groups.items():
        rows.sort(key=lambda r:(r['mean_ms'],r['failure_rate'],r['backend']));pareto=[];best=float('inf')
        for r in rows:
            if r['failure_rate']<best:pareto.append(r);best=r['failure_rate']
        fig,ax=plt.subplots(figsize=(10,5))
        for r in rows:ax.scatter(r['mean_ms'],r['failure_rate'],s=20);ax.annotate(r['backend'],(r['mean_ms'],r['failure_rate']),fontsize=5)
        ax.step([r['mean_ms'] for r in pareto],[r['failure_rate'] for r in pareto],where='post',color='black',label='Observed validation point envelope')
        ax.set(xscale='log',xlabel='Prepared online mean latency ms (one core)',ylabel='Any-observable failure rate',title=work+'; validation only, not an inferential frontier');ax.legend(fontsize=7);fig.tight_layout();fig.savefig(path/(work+'_pareto_envelope.png'),dpi=170);plt.close(fig)
        for budget in [1,10,100,1000]:
            feasible=[r for r in rows if r['mean_ms']<=budget]
            families=collections.defaultdict(list)
            for r in feasible:families[r['config']['kind']].append(r)
            choices={f:min(rr,key=lambda r:(r['failures'],r['mean_ms'])) for f,rr in families.items()}
            results.append(dict(workload=work,mean_budget_ms=budget,choices=choices,criterion='fastest tied minimum observed validation failure count under mean latency budget; no per-shot deadline, no independent-test winner selection'))
    atomic(ROOT/'evidence/validation_latency_budget_envelopes.json',dict(budgets_ms=[1,10,100,1000],results=results,scope='descriptive validation only; uncertainty and incomplete points in source analysis; not matched-quality superiority'))
if __name__=='__main__':main()
