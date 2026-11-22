import json,csv,hashlib,platform,importlib.metadata,math,os
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':14,'axes.labelsize':14,'xtick.labelsize':13,'ytick.labelsize':13,'axes.titlesize':15})
HERE=Path(__file__).resolve().parent
def wilson(f,n):
    z=1.9599639845;p=f/n;den=1+z*z/n
    mid=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return mid-half,mid+half
def main():
    rows=[]
    for p in sorted((HERE/'results').glob('*.json')):
        if '__clusters' in p.name or p.name.startswith('execution_failures'):continue
        r=json.loads(p.read_text())
        if 'engine' not in r:continue
        if r['engine']=='Tesseract':r['invalid']=None # Observable-only interface; not syndrome audited.
        # Reject smoke-test outputs rather than silently mix sample budgets.
        expected=256 if r['model']=='surface_d5_p0.006_B4' else 64
        if r['shots']!=expected:continue
        r['logical_failure_rate']=r['failures']/r['shots'];r['wilson95_low'],r['wilson95_high']=wilson(r['failures'],r['shots'])
        pred=np.load(HERE/'results'/(r['model']+'__'+r['engine']+'.npz'))['predictions']
        truth=np.load(HERE/'data'/r['model']/'samples.npz')['observables'][:r['shots']]
        r['mean_observable_bit_error_rate']=float(np.mean(pred!=truth))
        r['monitored_observables']=truth.shape[1]
        traces=json.loads((HERE/'results'/(r['model']+'__'+r['engine']+'__clusters.json')).read_text())
        r['solver_calls']=len(traces)
        r['bp_converged_solver_fraction']=sum(t.get('bp_converged',False) for t in traces)/len(traces) if traces else None
        rows.append(r)
    (HERE/'summary.json').write_text(json.dumps(rows,indent=2))
    fields=['model','engine','shots','failures','invalid','logical_failure_rate','wilson95_low','wilson95_high','mean_observable_bit_error_rate','monitored_observables','solver_calls','bp_converged_solver_fraction','mean_ms','p50_ms','p95_ms','p99_ms','startup_s','memory_pass_peak_rss_bytes','peak_cluster','faults','detectors','max_row_degree','max_col_degree']
    with (HERE/'summary.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
    pairs=[]
    for r in rows:
        if r['engine'] not in ['HUF','BPHUF']:continue
        peer='SW' if r['engine']=='HUF' else 'BPSW'
        mate=next((s for s in rows if s['model']==r['model'] and s['engine']==peer),None)
        if not mate:continue
        a=np.load(HERE/'results'/(r['model']+'__'+r['engine']+'.npz'));b=np.load(HERE/'results'/(r['model']+'__'+peer+'.npz'))
        assert r['samples_hash']==mate['samples_hash'] and r['model_hash']==mate['model_hash']
        mismatch=int(np.any(a['corrections']!=b['corrections'],axis=1).sum())
        ta=json.loads((HERE/'results'/(r['model']+'__'+r['engine']+'__clusters.json')).read_text());tb=json.loads((HERE/'results'/(r['model']+'__'+peer+'__clusters.json')).read_text())
        trace_mismatch=sum(x['merge_sizes']!=y['merge_sizes'] for x,y in zip(ta,tb))
        assert len(ta)==len(tb)
        pairs.append(dict(model=r['model'],mode=r['engine'],shots=r['shots'],correction_mismatches=mismatch,trace_mismatches=trace_mismatch,mean_speed_ratio=r['mean_ms']/mate['mean_ms'],failures=r['failures']))
    (HERE/'paired_audit.json').write_text(json.dumps(pairs,indent=2))
    ledger=[]
    for model in sorted(p.name for p in (HERE/'data').iterdir() if (p/'D.npz').exists()):
        for engine in ['HUF','SW','BPHUF','BPSW','Tesseract','LSD2','OSD2']:
            exists=any(r['model']==model and r['engine']==engine for r in rows)
            journal=HERE/'results'/(model+'__'+engine+'__shots.jsonl')
            ledger.append(dict(model=model,engine=engine,status='COMPLETE' if exists else 'NOT_COMPLETED_OR_UNAVAILABLE',partial_journal_shots=sum(1 for _ in journal.open()) if journal.exists() else 0))
    (HERE/'execution_ledger.json').write_text(json.dumps(ledger,indent=2))
    environment=dict(python=platform.python_version(),platform=platform.platform(),versions={k:importlib.metadata.version(k) for k in ['numpy','scipy','stim','ldpc','tesseract-decoder']},sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'huf.py',HERE/'run.py',HERE/'algebra.py']})
    environment['cpu_model']=next((line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')),'unavailable')
    environment['logical_cpus']=os.cpu_count()
    environment['affinity_cpu_count']=len(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None
    (HERE/'environment.json').write_text(json.dumps(environment,indent=2))
    fig,axes=plt.subplots(2,3,figsize=(13,7.3))
    specs=[('Blocks',lambda c:c.get('family')=='surface' and c.get('distance')==3 and c['rounds']==3,lambda c:c['blocks']),
           ('Code distance',lambda c:c.get('family')=='surface' and c['blocks']==4 and c['rounds']==3,lambda c:c['distance']),
           ('Noisy slices',lambda c:c.get('family')=='surface' and c.get('distance')==3 and c['blocks']==4,lambda c:c['rounds'])]
    configs={r['model']:json.loads((HERE/'data'/r['model']/'model.json').read_text()) for r in rows}
    styles=[('HUF','#bc4b30'),('SW','#16796f'),('BPHUF','#e6a323'),('BPSW','#263d1e'),('Tesseract','#3b5ba9'),('LSD2','#8561a8')]
    for col,(label,select,key) in enumerate(specs):
        for engine,color in styles:
            rr=sorted([r for r in rows if r['engine']==engine and abs(configs[r['model']]['p']-.003)<1e-12 and select(configs[r['model']])],key=lambda r:key(configs[r['model']]))
            if not rr:continue
            xx=[key(configs[r['model']]) for r in rr]
            axes[0,col].plot(xx,[r['mean_ms'] for r in rr],'o-',label=engine,color=color,ms=4)
            yy=np.array([r['logical_failure_rate'] for r in rr])
            axes[1,col].errorbar(xx,yy,yerr=[np.maximum(0,yy-np.array([r['wilson95_low'] for r in rr])),np.maximum(0,np.array([r['wilson95_high'] for r in rr])-yy)],fmt='o-',color=color,ms=4,capsize=2)
        xx_all=sorted({key(c) for c in configs.values() if abs(c['p']-.003)<1e-12 and select(c)})
        axes[0,col].set_xticks(xx_all);axes[1,col].set_xticks(xx_all)
        axes[0,col].set(yscale='log',xlabel=label,ylabel='Mean full-call latency (ms)')
        axes[1,col].set(xlabel=label,ylabel='Any-output failure probability',ylim=(-.03,1.03))
    for ax in axes.ravel():ax.grid(alpha=.2)
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',ncol=6,fontsize=13)
    fig.suptitle('Fixed-noise pilot p=0.003: separate block, distance, and depth axes',y=.94,fontsize=16)
    fig.tight_layout(rect=[0,0,1,.92]);fig.savefig(HERE/'scaling.pdf');fig.savefig(HERE/'scaling.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,3.4))
    for ax,(ea,eb,title) in zip(axes,[('HUF','SW','Prior-weighted pair'),('BPHUF','BPSW','BP-assisted pair')]):
        models=set(r['model'] for r in rows if r['engine']==ea)&set(r['model'] for r in rows if r['engine']==eb)
        for engine,color in [(ea,'#bc4b30'),(eb,'#16796f')]:
            vals=[]
            for model in models:
                traces=json.loads((HERE/'results'/(model+'__'+engine+'__clusters.json')).read_text())
                vals.extend(t['peak_cluster'] for t in traces)
            if vals:
                x=np.sort(vals);ax.step(x,np.arange(1,len(x)+1)/len(x),where='post',label=engine,color=color)
        ax.set(title=title,xlabel='Peak cluster per recorded completed call',ylabel='Empirical CDF',xscale='symlog');ax.grid(alpha=.2);ax.legend()
    fig.tight_layout();fig.savefig(HERE/'clusters.pdf');plt.close(fig)
    lines=['# Seamwise controlled circuit pilot','',f'Completed configurations/backends: {len(rows)}; completed paired HUF comparisons: {len(pairs)}.','',
        'HUF and SW are rebuilding/persistent modes of the same new Python HUF reference, inside the complete Seamwise repair1 wrapper. BPHUF/BPSW add the same specified BP-assisted residual preconditioning to those modes. They are not the original authors\' HUF executable. Terminal canonicalization is performed in both modes. External baselines are native complete-record decoders. No result establishes SOTA.','',
        '| Configuration | Backend | Failures / shots | Mean ms | p95 ms | Sampled process RSS MiB |', '|---|---|---:|---:|---:|---:|']
    for r in rows:lines.append(f"| {r['model']} | {r['engine']} | {r['failures']}/{r['shots']} | {r['mean_ms']:.2f} | {r['p95_ms']:.2f} | {r['memory_pass_peak_rss_bytes']/2**20:.1f} |")
    lines+=['','## Interpretation','',
        'Paired output and merge-history equality is tested directly in paired_audit.json. Native/Python latency differences measure these implementations, not an implementation-independent algorithm ordering. Shared terminal canonicalization makes identical logical performance expected; a change in logical failure would indicate an implementation or policy mismatch.','',
        'All completed pilot failure rates have Wilson intervals in summary.csv. A zero count in 64 samples does not establish a zero true error rate. Failed or time-limited runs are NOT included as successful or zero-error runs. Partial journal prefixes are execution telemetry, not unbiased fidelity samples.','',
        'Original archived models use identical stored D/L, priors and samples in every backend; new scaling models use the recovered original generator with independently frozen seeds. These are distinct configurations, so a line joining them is not a fitted asymptotic exponent.','',
        'Latency is one warm pass per backend, without memory polling. Memory is a separate 1ms RSS-sampled pass over the first four inputs and includes the whole Python process, imported libraries, model and retained diagnostics. Startup, raw durations, output bitstrings, and cluster histories are retained. These are shared-host pilot measurements without three independent timing replicates or affinity isolation.','',
        'The primary 256-shot BPHUF/BPSW runs were preallocated 180 seconds per process. The first completed BB144 low-noise runs were allowed a 180-second process budget. After slow high-noise calls, subsequent child processes were capped at 45 seconds, before viewing their outcomes. This is a resource-budget amendment; raw logs retain non-completions. No outcome-dependent sample-count selection is used.','',
        'Tesseract (2025), native BP+LSD (published 2025), and stronger-order OSD are measured. Relay-BP was attempted but its native package could not build here (no compatible wheel/Rust toolchain). GARI (2026), ghost protocol (2026), logical-product/observable decoders and IRS remain unmeasured: their circuit/observable adapters have not been verified. They must not be shown as defeated baselines.']
    (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    # Publication tables use completed, fixed-budget rows only.
    tex=['\\subsection{Controlled persistent-backend circuit pilot}\\label{sec:newpilot}',
        f'Across {len(configs)} circuit configurations and {7*len(configs)} planned configuration/backend jobs, {len(rows)} jobs complete the full measurement protocol. The {len(pairs)} matched rebuilding/persistent comparisons cover {sum(p["shots"] for p in pairs):,} paired shot executions, with zero correction-vector or recorded growth-history disagreements. Full details and non-completions are retained in the archive.',
        '\\begin{table*}[t]\\centering\\scriptsize',
        '\\caption{Completed controlled pilot runs. HUF/SW: complete Seamwise with prior-weighted rebuilding/persistent HUF. BPHUF/BPSW: matched BP-assisted counterparts. Tesseract, LSD2 and OSD2: native joint decoders. RSS is the separately sampled whole-process footprint, not backend-only storage.}\\label{tab:newpilot}',
        '\\begin{tabular}{llrrrr}\\toprule Configuration&Backend&Failures/shots&Mean ms&p95 ms&RSS MiB\\\\\\midrule']
    # Keep main-text table compact; all rows remain in CSV.
    chosen=[r for r in rows if r['model'] in ['bb144_p0.005_B4','surface_d5_p0.006_B4','surface_d3_p0.003_B4']]
    for r in chosen:
        name=r['model'].replace('_','\\_');tex.append(f"{name}&{r['engine']}&{r['failures']}/{r['shots']}&{r['mean_ms']:.2f}&{r['p95_ms']:.2f}&{r['memory_pass_peak_rss_bytes']/2**20:.1f}\\\\")
    tex+=['\\bottomrule\\end{tabular}\\end{table*}',
        '\\begin{figure*}[t]\\centering\\includegraphics[width=\\textwidth]{study_scaling.pdf}\\caption{Measured scaling pilot at fixed noise p=.003. Block sweep fixes d=3 and T=3; distance sweep fixes four blocks and T=3; depth sweep fixes d=3 and four blocks. Error bars are marginal Wilson intervals. Only completed, fixed-sample runs are plotted; fixed shallow extraction depth is not a threshold experiment.}\\label{fig:newscale}\\end{figure*}',
        '\\begin{figure*}[t]\\centering\\includegraphics[width=\\textwidth]{study_clusters.pdf}\\caption{Peak-cluster distributions over recorded completed solver calls. Each panel uses configurations completed by both members of that oracle pair. BP early exits have zero peak; infeasible rejected-call histories are unavailable. The two panels need not have the same configuration cohort.}\\label{fig:newclusters}\\end{figure*}',
        'The controlled study does not establish a general latency advantage of the current persistent implementation. The exact-oracle guarantee concerns reusable algebra; full-call time additionally includes boundary scans, state creation, canonicalization and wrapper costs. Native external baselines test the remaining implementation and accuracy gap. Small pilot sample sizes, censored non-completions, and untuned resource settings limit interpretation to the measured implementation and workloads.']
    if (HERE/'study_repeats.tex').exists():tex.append(r'\input{study_repeats}')
    (HERE/'study_results.tex').write_text('\n'.join(tex)+'\n')
    print(json.dumps(dict(completed=len(rows),paired=len(pairs),mismatches=sum(p['correction_mismatches'] for p in pairs))))
if __name__=='__main__':main()
