import csv,json,hashlib
from pathlib import Path
import numpy as np
here=Path(__file__).resolve().parent
rows=json.loads((here/'timing_replicates'/'summary.json').read_text())
summary=[];gains=[]
tex=[r'\subsection{Independent-process timing replication}',r'Three fresh-process replicates follow the controlled pilot at the primary surface-code point and the high-noise BB144 point. Each uses the same first 64 inputs with randomized method order. These are additional timing executions, not new independent logical samples. All repeated predictions match the corresponding stored single-pass predictions.']
tex += [r'\begin{table*}[t]\centering\scriptsize',r'\caption{Three independently initialized timing replicates on 64 reused inputs per operating point. RSS is the maximum separately sampled whole-process footprint across replicates.}\label{tab:replication}',r'\begin{tabular}{llrrrrr}\toprule Point&Backend&Run 1 mean ms&Run 2&Run 3&Pooled p95 ms&Max RSS MiB\\\midrule']
for model in sorted(set(r['model'] for r in rows)):
    byrep={}
    for engine in ['BPHUF','BPSW','Tesseract']:
        a=sorted([r for r in rows if r['model']==model and r['engine']==engine],key=lambda r:r['replicate'])
        assert len(a)==3
        ns=np.concatenate([np.load(here/'timing_replicates'/r['replicate']/(model+'__'+engine+'.npz'))['latency_ns'] for r in a])/1e6
        rec=dict(model=model,engine=engine,replicate_means_ms=[r['mean_ms'] for r in a],median_mean_ms=float(np.median([r['mean_ms'] for r in a])),pooled_p95_ms=float(np.quantile(ns,.95)),max_sampled_rss_mib=max(r['memory_pass_peak_rss_bytes']/2**20 for r in a))
        summary.append(rec)
        short='Surface d5' if model.startswith('surface') else 'BB144'
        tex.append(f"{short}&{engine}&{a[0]['mean_ms']:.2f}&{a[1]['mean_ms']:.2f}&{a[2]['mean_ms']:.2f}&{rec['pooled_p95_ms']:.2f}&{rec['max_sampled_rss_mib']:.1f}\\\\")
        byrep[engine]={r['replicate']:r['mean_ms'] for r in a}
    reductions=[1-byrep['BPSW'][k]/byrep['BPHUF'][k] for k in byrep['BPHUF']]
    gains.append(dict(model=model,paired_relative_reductions=reductions,median_relative_reduction=float(np.median(reductions))))
tex += [r'\bottomrule\end{tabular}\end{table*}']
profile=json.loads((here/'profile_summary.json').read_text())
x,y=profile[0]['basis_insertion_calls'],profile[1]['basis_insertion_calls']
tex += [f"The median paired reduction in mean latency is {100*gains[1]['median_relative_reduction']:.1f}\\% at the surface-code point and {100*gains[0]['median_relative_reduction']:.1f}\\% at the BB144 point. The corresponding whole-process RSS measurements show little change between oracle modes. Native Tesseract remains a stronger accuracy comparator on these samples; the timing table also exposes dependence on which fixed sample subset is measured.",f"A separate diagnostic on eight fixed high-noise BB144 inputs records {x:,} rebuilding basis-insertion calls and {y:,} persistent calls, a {x/y:.1f}-fold reduction in this repeated-column-processing counter. Both diagnostic outputs are identical. The instrumented times are excluded from benchmark latency. Profiling identifies repeated component creation, DSU root queries and eligibility scans as substantial remaining costs; those paths are preserved by the current oracle replacement."]
(here/'study_repeats.tex').write_text('\n'.join(tex)+'\n')
(here/'replication_summary.json').write_text(json.dumps(dict(rows=summary,gains=gains),indent=2))
with (here/'replication_summary.csv').open('w') as f:
    writer=csv.DictWriter(f,fieldnames=['model','engine','median_mean_ms','pooled_p95_ms','max_sampled_rss_mib'],extrasaction='ignore');writer.writeheader();writer.writerows(summary)
source={str(p.relative_to(here)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(here.rglob('*.py')) if '__pycache__' not in p.parts}
inputs={str(p.relative_to(here)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((here/'data').rglob('*')) if p.is_file()}
(here/'source_manifest.json').write_text(json.dumps(source,indent=2));(here/'input_manifest.json').write_text(json.dumps(inputs,indent=2))
report=(here/'RESULTS.md').read_text().split('## Three-process replication and structural diagnostic')[0].rstrip()+'\n'
report+='\n## Three-process replication and structural diagnostic\n\n'
for g in gains:report+=f"- {g['model']}: median paired mean-latency reduction {100*g['median_relative_reduction']:.1f}%; three randomized-order fresh-process runs on the same 64 inputs.\n"
report+=f'\nEight-input BB144 diagnostic: {x:,} versus {y:,} basis insertion calls ({x/y:.1f}x fewer). This is a routine-call counter, not a measured word-operation count or end-to-end speedup. Root queries, component allocation and eligibility scans remain substantial in the saved profiles.\n'
report+='\nWhole-process RSS changes little between oracle modes. The first-64 primary timing repetitions make Tesseract faster than the persistent reference on that subset, while its full-256 mean is larger because the input set differs. These results do not support an unconditional performance ordering. See replication_summary.csv and full per-shot durations.\n'
(here/'RESULTS.md').write_text(report)
print(json.dumps(dict(gains=gains,profile_reduction_factor=x/y,replicate_runs=len(rows))))
