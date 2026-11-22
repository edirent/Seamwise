#!/usr/bin/env python3
"""Additional descriptive controls, lifecycle and current diagnostic evidence."""
import sys,pathlib,json,collections
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from seamwise_bench.common import ROOT,atomic
from seamwise_bench.analysis import read_run,timing_ratio

def main():
    index=json.loads((ROOT/'evidence/run_index.json').read_text());groups,_=read_run(ROOT/index['primary_timing']);rows=[]
    rng=np.random.default_rng(620261109)
    for (work,name),records in groups.items():
        times=np.array([[r['latency_ns'] for r in rr] for _,rr in records]);tail=[]
        for _ in range(600):
            reps=rng.integers(len(times),size=len(times));ids=rng.integers(times.shape[1],size=times.shape[1]);tail.append(np.quantile(times[np.ix_(reps,ids)],.99)/1e6)
        rows.append(dict(workload=work,backend=name,p99_ms=float(np.quantile(times,.99)/1e6),p99_pointwise95=np.quantile(tail,[.025,.975]).tolist(),
            preparation_ms=[j['preparation_ns']/1e6 for j,_ in records],load_prepare_ms=[j['load_prepare_ns']/1e6 for j,_ in records],
            lifecycle_decoder_work_ms=[j['lifecycle_decoder_work_ns']/1e6 for j,_ in records],lifecycle_calls=[j['lifecycle_decoder_calls'] for j,_ in records],
            uncertainty='paired repetition blocks and sample IDs, 600 draws; tail resolution limited by 1024 independent inputs',
            binding_overhead='UNAVAILABLE as an isolated term; Python adapter/binding conversions included in all headline prepared-online times'))
    # Amortization comparisons use observed load/prepare and decode means;
    # they are work estimates, not wall time inclusive of research I/O.
    crossover=[]
    for work in sorted({k[0] for k in groups}):
        def stats(name):
            rec=groups[(work,name)];return np.mean([j['load_prepare_ns'] for j,_ in rec]),np.mean([r['latency_ns'] for _,rr in rec for r in rr])
        ar,at=stats('native_rebuild');br,bt=stats('native_persistent');delta=at-bt
        crossover.append(dict(workload=work,A='native_rebuild',B='native_persistent',load_prepare_A_ns=float(ar),load_prepare_B_ns=float(br),
            online_A_ns=float(at),online_B_ns=float(bt),B_break_even_shots=float(max(0,(br-ar)/delta)) if delta>0 else None,
            lifecycle_estimates=[dict(shots=n,A_ms=float((ar+n*at)/1e6),B_ms=float((br+n*bt)/1e6)) for n in [1,16,1024,10000]],
            scope='observed fixed-1024-corpus load/prepare overhead plus n online calls; excludes warmup, sample generation, external audit and serialization. Loading is not remeasured for each N, so these are exploratory work estimates, not exact lifecycle wall-time measurements.'))
    atomic(ROOT/'evidence/lifecycle_and_tail_analysis.json',dict(rows=rows,crossover=crossover))
    controls=[]
    for key in ['optimization','rebuild_fairness']:
        g,missing=read_run(ROOT/index[key]);bywork=collections.defaultdict(dict)
        for (work,name),rec in g.items():bywork[work][name]=sorted(rec,key=lambda z:z[0]['repetition'])
        for work,points in bywork.items():
            anchor=points.get('build_persistent') or next(iter(points.values()))
            for name,rec in points.items():
                assert len(rec)==len(anchor)
                for (_,aa),(_,bb) in zip(anchor,rec):
                    assert [r['sample_id'] for r in aa]==[r['sample_id'] for r in bb]
                    assert [r['correction_sha256'] for r in aa]==[r['correction_sha256'] for r in bb]
                controls.append(dict(run=index[key],workload=work,backend=name,exact_correction_equality=True,mean_ms=float(np.mean([r['latency_ns'] for _,rr in rec for r in rr])/1e6)))
    atomic(ROOT/'evidence/compiled_revision_exact_audit.json',controls)
    agroups,_=read_run(ROOT/index['accuracy']);test_audits=[];marginals=[]
    for work in sorted({k[0] for k in agroups}):
        ar=agroups.get((work,'native_rebuild'));br=agroups.get((work,'native_persistent'))
        if ar and br:
            aa,bb=ar[0][1],br[0][1]
            assert [r['sample_id'] for r in aa]==[r['sample_id'] for r in bb]
            assert [r['correction_sha256'] for r in aa]==[r['correction_sha256'] for r in bb]
            test_audits.append(dict(workload=work,shots=len(aa),exact_corrections=True,extra_independent_accuracy_samples=0))
    for (work,name),rec in agroups.items():
        rr=rec[0][1];mat=np.array([r['marginal_observable_failures'] for r in rr])
        marginals.append(dict(workload=work,backend=name,n_circuit_shots=len(rr),any_observable_failures=sum(r['logical_failure'] for r in rr),
            per_observable_failure_counts=mat.sum(axis=0).tolist(),denominator='same N circuit shots for each individual observable; any-observable remains the primary rate'))
    atomic(ROOT/'evidence/independent_test_exact_oracle_audit.json',test_audits)
    atomic(ROOT/'evidence/marginal_observable_rates.json',marginals)
    path=ROOT/index['profiles'];profiles=[]
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for f in path.glob('*_per_shot.json'):
        data=json.loads(f.read_text());diagnostics=json.loads(f.with_name(f.name.replace('_per_shot','_diagnostics')).read_text())
        fig,axs=plt.subplots(1,2,figsize=(11,4))
        for key in ['largest_detectors','largest_faults','largest_rank','largest_incidences']:
            vals=np.sort([r[key] for r in data]);axs[0].step(vals,np.arange(1,len(vals)+1)/len(vals),where='post',label=key)
        for convergence in [False,True]:
            selected=[r for r in data if bool(r['operation_counts'].get('bp_converged',0))==convergence]
            if selected:
                vals=np.sort([r['largest_vertices'] for r in selected]);axs[1].step(vals,np.arange(1,len(vals)+1)/len(vals),label=f'any local BP converged={convergence}, N={len(vals)}')
        for ax in axs:ax.set(xlabel='Per circuit-shot maximum; BP-only exits contribute zero',ylabel='CDF');ax.legend(fontsize=6)
        fig.suptitle(f.stem+'; validation diagnostic, includes failed local calls');fig.tight_layout();fig.savefig(f.with_suffix('.png'),dpi=150);plt.close(fig)
        profiles.append(dict(file=str(f.relative_to(ROOT)),shots=len(data),wrapper=diagnostics['wrapper'],local_counts=[s['counts'] for s in diagnostics['solvers']],
            counts_scope='root/eligibility/frontier/algebra/terminal/BP per local call; cut/repair wrapper intervals contain local stages and cannot be added to them',
            trace_coverage='all instrumented local histories, including infeasible attempts; BP early exits have no growth merges',
            unavailable='isolated acceptance-decision and binding timers; use whole wrapper intervals and native gprof call graph, not invented exclusive percentages'))
    atomic(ROOT/'evidence/current_profile_analysis.json',profiles)
if __name__=='__main__':main()
