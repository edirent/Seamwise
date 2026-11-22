#!/usr/bin/env python3
"""Reconstruct final growth components from canonical semantic merge events."""
import pathlib,sys,json
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from seamwise_bench.common import ROOT,atomic
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
idx=json.loads((ROOT/'evidence/run_index.json').read_text());out=ROOT/idx['profiles'];summary=[]
for p in out.glob('*_diagnostics.json'):
    if p.stem.endswith('_per_shot_diagnostics'):continue
    d=json.loads(p.read_text());components=[];merges=[];ranks=[];failed=0
    for si,solver in enumerate(d['solvers']):
        for hi,h in enumerate(solver['histories']):
            states={};failed+=not h['success'];ranks+=h['final_ranks']
            assert len(h['semantic_merges'])==len(h['merge_sizes'])
            for i,event in enumerate(h['semantic_merges']):
                a,b,label,size=event[:4];old_a=states.pop(a,dict(vertices=1));old_b=states.pop(b,dict(vertices=1))
                assert a!=b and label==min(a,b) and old_a['vertices']+old_b['vertices']==size
                states[label]=dict(vertices=size,detectors=h['merge_detectors'][i],faults=h['merge_faults'][i],incidences=h['merge_incidences'][i])
                assert states[label]['detectors']+states[label]['faults']==size
            components.extend(dict(v,solver_id=si,local_history_id=hi,canonical_label=label,local_success=h['success']) for label,v in states.items())
            merges+=h['merge_sizes']
    stem=p.stem.removesuffix('_diagnostics');shots=json.loads((out/(stem+'_per_shot.json')).read_text())
    fig,ax=plt.subplots(figsize=(9,5))
    for label,vals in [('each final non-singleton growth component',[c['vertices'] for c in components]),('each merge event',merges),('each circuit-shot maximum (BP exits=0)',[s['largest_vertices'] for s in shots])]:
        if vals:
            vals=np.sort(vals);ax.step(vals,np.arange(1,len(vals)+1)/len(vals),where='post',label=f'{label}; N={len(vals)}')
    ax.set(xlabel='Detector + fault vertices',ylabel='CDF',title=stem+'; denominators differ');ax.legend(fontsize=7);fig.tight_layout();fig.savefig(out/(stem+'_component_weighted_cdf.png'),dpi=150);plt.close(fig)
    times=[json.loads(line) for line in (out/(stem+'_native.jsonl')).read_text().splitlines()];assert len(times)==len(shots)
    lat=np.array([r['latency_ns']/1e6 for r in times]);sizes=np.array([r['largest_vertices'] for r in shots]);threshold=float(np.quantile(lat,.75));hard=lat>=threshold
    fig,ax=plt.subplots(figsize=(8,5));fallback=[bool(r['wrapper_counts']['fallback']) for r in shots]
    ax.scatter(sizes,lat,c=fallback,cmap='coolwarm');ax.set(xlabel='Per-shot maximum growth-cluster vertices (separate audit pass)',ylabel='Native gprof-process diagnostic latency ms',title=stem+'; same validation IDs, separate instrumented scopes');fig.tight_layout();fig.savefig(out/(stem+'_runtime_clusters.png'),dpi=150);plt.close(fig)
    record=dict(workload_mode=stem,components=components,terminal_component_ranks=ranks,failed_calls_without_terminal_rank=failed,
        component_denominator='one final non-singleton component per local growth call, including failed calls at abort; untouched singletons and BP-only exits excluded',
        shot_denominator='one maximum per circuit shot; BP-only exits contribute zero',
        history_to_individual_shot_map='UNAVAILABLE in aggregate histories; per-shot maxima and failed-call counts are recorded separately',
        difficult_shot_strata=dict(threshold_ms=threshold,hardest_quarter_n=int(hard.sum()),hardest_quarter_cluster_mean=float(sizes[hard].mean()),other_cluster_mean=float(sizes[~hard].mean()) if (~hard).any() else None),
        runtime_scope='same IDs in a separate native gprof process; explanatory association only, not publication online timing or a scaling-law fit')
    atomic(out/(stem+'_final_components.json'),record);summary.append({k:v for k,v in record.items() if k not in ['components','terminal_component_ranks']})
atomic(ROOT/'evidence/cluster_reconstruction_summary.json',summary)
