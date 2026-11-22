#!/usr/bin/env python3
"""Exploratory measurements on the pre-registered independent scaling fixtures."""
import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from seamwise_bench.common import ROOT,atomic,digest,sha,unique_run
from seamwise_bench.runner import run
from seamwise_bench.analysis import analyze

def main():
    source=ROOT/'results/20261109T190227Z-scaling-c07d24f0'
    entries=json.loads((source/'registry.json').read_text());out=unique_run('scaling-manifest');items={}
    for i,e in enumerate(entries):
        if e['status']!='PREPARED':continue
        p=ROOT/e['path'];hashes=e['hashes']
        assert all(sha(p/k)==h for k,h in hashes.items())
        modelhash=digest({k:h for k,h in hashes.items() if k!='validation.npz'})
        name=f"{i:02d}_{e['axis']}_{e['label']}"
        items[name]=dict(path=e['path'],model_hash=modelhash,model_files={k:h for k,h in hashes.items() if k!='validation.npz'},
            splits=dict(validation=dict(path=str((p/'validation.npz').relative_to(ROOT)),sha256=hashes['validation.npz'],shots=16,
                sample_id_prefix=f"{modelhash}:{e['metadata']['seed']}")),registry_entry=e)
    atomic(out/'manifest.json',dict(kind='frozen_circuit_samples',workloads=items,exploratory=True))
    config=dict(workloads=list(items),count=16,warmup=4,repetitions=1,backends=[dict(name='native_rebuild',kind='native',family='bphuf',policy='repair1',persistent=False),dict(name='native_persistent',kind='native',family='bphuf',policy='repair1',persistent=True)],
        budgets=dict(preparation=30,decode=45,memory=10),stage_wall_budgets=dict(validation=600),campaign_wall_budget_s=600)
    atomic(out/'config.json',config)
    result=run(out/'manifest.json',config,mode='validation',split='validation');a=analyze(result)
    rows=[]
    for r in a['summary']:
        entry=items[r['workload']]['registry_entry']
        rows.append(dict(r,axis=entry['axis'],label=entry['label'],metadata=entry['metadata']))
    atomic(result/'scaling_results.json',dict(rows=rows,incomplete=a['incomplete_jobs'],registry=str((source/'registry.json').relative_to(ROOT)),
        scope='16 circuit-sampled validation inputs; exploratory size/depth controls; one repetition; no threshold inference',deferred=[e for e in entries if e['status'] not in ['PREPARED','PREPARED_ALIAS','HISTORICAL_READ_ONLY']]))
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for axis in sorted({r['axis'] for r in rows}):
        fig,axs=plt.subplots(1,2,figsize=(12,4))
        for backend in ['native_rebuild','native_persistent']:
            selected=[r for r in rows if r['axis']==axis and r['backend']==backend]
            for ax,key in zip(axs,['detectors','incidences']):
                selected.sort(key=lambda r:r['metadata'][key]);ax.plot([r['metadata'][key] for r in selected],[r['mean_ms'] for r in selected],'o-',label=backend)
                for r in selected:ax.annotate(r['label'],(r['metadata'][key],r['mean_ms']),fontsize=6)
                ax.set(xlabel=key,ylabel='Prepared online mean ms');ax.legend(fontsize=7)
        fig.suptitle(axis+'; N=16, exploratory');fig.tight_layout();fig.savefig(result/(axis+'_scaling.png'),dpi=150);plt.close(fig)
    atomic(ROOT/'evidence/scaling_measurement_index.json',dict(run=str(result.relative_to(ROOT))))
    print(result)
if __name__=='__main__':main()
