#!/usr/bin/env python3
"""Evidence-backed report. Run after measurement workers finish."""
import sys,pathlib,json,math,collections
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from seamwise_bench.common import ROOT,atomic,sha
from seamwise_bench.analysis import analyze,read_run,paired,timing_ratio,cp_lower,cp_upper

WORKS=['bb144_p0.015_B4','surface_d3_p0.003_B4','surface_d5_p0.006_B4']

def latest(label):
    files=sorted((ROOT/'results').glob('*-'+label+'-*'))
    return files[-1] if files else None

def mean_ratio_report(path,numerator,denominator,exact=False):
    groups,missing=read_run(path);rows=[];arrays=[]
    for work in WORKS:
        a=sorted(groups[(work,numerator)],key=lambda x:x[0]['repetition']);b=sorted(groups[(work,denominator)],key=lambda x:x[0]['repetition'])
        if not a or not b or len(a)!=len(b):
            return dict(status='UNRESOLVED_INCOMPLETE',geometric_mean=None,missing_jobs=missing,workloads=rows)
        assert [j['repetition'] for j,_ in a]==[j['repetition'] for j,_ in b]
        assert all([r['sample_id'] for r in aa[1]]==[r['sample_id'] for r in bb[1]] for aa,bb in zip(a,b))
        if exact:
            assert all([r['correction_sha256'] for r in aa[1]]==[r['correction_sha256'] for r in bb[1]] for aa,bb in zip(a,b))
        av=np.array([[r['latency_ns'] for r in rr] for _,rr in a]);bv=np.array([[r['latency_ns'] for r in rr] for _,rr in b])
        rows.append(dict(workload=work,numerator=numerator,denominator=denominator,quality_constraint='exact correction SHA256 equality' if exact else 'frozen policy comparison',scope=a[0][0]['scope'],cores=1,threads=1,batch=1,
                         numerator_mean_ms=float(av.mean()/1e6),denominator_mean_ms=float(bv.mean()/1e6),speedup=timing_ratio(av,bv),input_ids=[r['sample_id'] for r in a[0][1]]))
        arrays.append((av,bv))
    rng=np.random.default_rng(20261109);boot=[]
    for _ in range(800):
        ratios=[]
        for a,b in arrays:
            rr=rng.integers(a.shape[0],size=a.shape[0]);ss=rng.integers(a.shape[1],size=a.shape[1]);ratios.append(a[np.ix_(rr,ss)].mean()/b[np.ix_(rr,ss)].mean())
        boot.append(math.exp(float(np.log(ratios).mean())))
    return dict(workloads=rows,geometric_mean=math.exp(sum(math.log(r['speedup']['ratio']) for r in rows)/len(rows)),
                aggregate_interval95=np.quantile(boot,[.025,.975]).tolist(),aggregate_simultaneous_interval9833=np.quantile(boot,[.05/6,1-.05/6]).tolist(),
                denominator='equal weight over all three predeclared workloads; fixed workload set',uncertainty='paired hierarchical sample-ID and repetition bootstrap, 800 draws; 98.33% intervals allow Bonferroni across three primary engineering aggregates',missing_jobs=missing)

def table(summary,fields):
    lines=['| '+' | '.join(label for key,label in fields)+' |','| '+' | '.join('---' for _ in fields)+' |']
    for row in summary:
        def value(key):
            v=row.get(key)
            if v is None:return 'UNAVAILABLE'
            if isinstance(v,(list,tuple)):
                return '['+', '.join(f'{x:.4g}' if isinstance(x,(float,np.floating)) else str(x) for x in v)+']'
            return f'{v:.4g}' if isinstance(v,float) else str(v)
        lines.append('| '+' | '.join(value(k) for k,l in fields)+' |')
    return '\n'.join(lines)

def main():
    index=json.loads((ROOT/'evidence/run_index.json').read_text());report={};sections=[]
    original=json.loads((ROOT/'evidence/original_sha256.json').read_text());changed=[p for p,h in original.items() if not (ROOT.parent/p).exists() or sha(ROOT.parent/p)!=h]
    if changed:raise RuntimeError('Historical integrity failed: '+str(changed))
    report['historical_integrity']=dict(files=len(original),changed=changed)
    regression=json.loads((ROOT/index['historical_regression']/'regression.json').read_text());report['historical_regression']=dict(statuses=dict(collections.Counter(r['status'] for r in regression)),exact_executions=sum(r.get('shots',0) for r in regression if r['status']=='PASS'))
    engineer=ROOT/index['engineering'];port_r=mean_ratio_report(engineer,'python_rebuild','native_rebuild',True);port_p=mean_ratio_report(engineer,'python_persistent','native_persistent',True)
    report['S_port_rebuild']=port_r;report['S_port_persistent']=port_p
    sections.append('# Seamwise native framework: measured results\n\nOriginal data and manuscript files are unchanged. All measurements are from the same virtualized host, one pinned CPU / decoder thread, batch one; no bare-metal claim. Completed, deferred, failed and partial jobs remain distinct.\n')
    sections.append('## Correctness and provenance gates\n\nThe native suite passed 1,968 exhaustive/seeded cases, including 100 exact flat-versus-official BP LLR/iteration comparisons. The final C++ source passed ASan/UBSan/leak checks; 11 Python/model/adapter/watchdog contracts passed. Differential gates require exact corrections, repair decisions and semantic growth IDs, with reversed/shuffled/reset/fresh-worker checks. Independent test rebuild/persistent outputs also match exactly on all 30,000 circuit IDs across the three workloads. See `evidence/postcampaign_integrity.json`: frozen decoder sources and the native module stayed identical through timing, accuracy and the repaired memory pass. Installed official Tesseract/Relay binary members match their pinned local source wheels byte-for-byte (`evidence/installed_official_wheel_equivalence.json`).\n')
    sections.append(f"## Engineering port\n\nOn 128 shared validation IDs per workload and three fresh processes, the equal-workload geometric means are **{port_r['geometric_mean']:.3f}x** for Python rebuild / native rebuild and **{port_p['geometric_mean']:.3f}x** for Python persistent / native persistent. Exact correction hashes match. These are exploratory implementation measurements; they exceed the 2x-5x engineering target on this declared cohort. Persistence is measured separately.\n")
    rows=[]
    for mode,r in [('rebuild',port_r),('persistent',port_p)]:
        for x in r['workloads']:rows.append(dict(mode=mode,workload=x['workload'],python_ms=x['numerator_mean_ms'],native_ms=x['denominator_mean_ms'],speedup=x['speedup']['ratio']))
    sections.append(table(rows,[('mode','Mode'),('workload','Workload'),('python_ms','Python mean ms'),('native_ms','Native mean ms'),('speedup','S_port')]))
    sections.append(f"\nHierarchical aggregate 95% intervals: rebuild {port_r['aggregate_interval95']}, persistent {port_p['aggregate_interval95']}. Simultaneous 98.33% intervals across the three engineering aggregates: rebuild {port_r['aggregate_simultaneous_interval9833']}, persistent {port_p['aggregate_simultaneous_interval9833']}. Workload identities remain fixed, with equal weights; sample IDs and fresh-process repetitions are resampled.\n")
    timing=ROOT/index['primary_timing'];timing_analysis=analyze(timing);persist=mean_ratio_report(timing,'native_rebuild','native_persistent',True);report['S_persist']=persist
    sections.append(f"\n## Native persistence ablation\n\nPrepared-online `S_persist = T_native_rebuild / T_native_persistent`, with the same graph frontend, BP, scheduling, compiler flags, full-witness oracle contract and canonical terminal solve, is **{persist['geometric_mean']:.3f}x** geometrically across the full three-workload set. The independent timing corpus has 1,024 IDs and seven fresh process repetitions. It does not add 7,168 independent accuracy samples.\n")
    sections.append(table([dict(workload=r['workload'],ratio=r['speedup']['ratio'],ci=r['speedup']['interval']) for r in persist['workloads']],[('workload','Workload'),('ratio','S_persist'),('ci','Pointwise 95% bootstrap interval')]))
    sections.append(f"\nAggregate 95% interval: {persist['aggregate_interval95']}; simultaneous 98.33% interval: {persist['aggregate_simultaneous_interval9833']}. A ratio below one is a regression. The selected full-method point can use a different repair policy (BB144 repair2); it is not substituted into the repair1 persistence ablation.\n")
    sections.append('\n'+table(timing_analysis['summary'],[('workload','Workload'),('backend','Backend'),('mean_ms','Mean ms'),('median_ms','Median ms'),('p95_ms','p95 ms'),('p99_ms','p99 ms'),('max_ms','Max ms')]))
    bypoint={(r['workload'],r['backend']):r for r in timing_analysis['summary']};tails=[]
    for work in WORKS:
        a=bypoint[(work,'native_rebuild')];b=bypoint[(work,'native_persistent')]
        tails.append(dict(workload=work,persistent_mean_over_rebuild=b['mean_ms']/a['mean_ms'],persistent_p99_over_rebuild=b['p99_ms']/a['p99_ms'],mean_regressed=b['mean_ms']>a['mean_ms'],p99_regressed=b['p99_ms']>a['p99_ms']))
    report['native_tail_tradeoffs']=tails
    sections.append('\n'+table(tails,[('workload','Workload'),('persistent_mean_over_rebuild','Persistent/rebuild mean'),('persistent_p99_over_rebuild','Persistent/rebuild p99'),('mean_regressed','Observed mean regression'),('p99_regressed','Observed p99 regression')]))
    sections.append('\nThese descriptive regression flags compare pooled latency estimators; they are not individual significance tests. Per-repetition p99 values and hierarchical p99 intervals are retained separately.\n')
    accuracy=ROOT/index['accuracy'];acc=analyze(accuracy);report['accuracy']=acc
    sections.append('\n## Independent accuracy and frontier gates\n\nFixed requested N is 10,000 circuit shots per workload, with disjoint validation, timing and test streams. Logical failure is any observable disagreement. Invalid corrections/service failures are separate. Wilson intervals, paired discordance tables and conservative simultaneous exact-cell bounds are retained in analysis.json. The relative noninferiority margin is **10%**, not identical accuracy; strict equality-target bounds are also saved. No finite failure-rate ratio is inferred from two zero counts.\n')
    sections.append(table(acc['summary'],[('workload','Workload'),('backend','Backend'),('n_independent','N'),('failures','Logical failures'),('service_failures','Invalid/service'),('failure_rate','Rate'),('wilson95','Wilson 95%'),('precision','Precision planning')]))
    selected_counts={r['workload']:r['failures'] for r in acc['summary'] if r['backend']=='seamwise_selected'}
    reference_counts={r['workload']:r['failures'] for r in acc['summary'] if r['backend']=='tuned_tesseract'}
    sections.append('\nThe observed selected Seamwise / frozen Tesseract logical-failure counts are '+', '.join(f"{w}: **{selected_counts.get(w,'INCOMPLETE')} / {reference_counts.get(w,'INCOMPLETE')}**" for w in WORKS)+'. Every completed point uses the same 10,000 circuit IDs within its workload. These negative quality results remain part of the main result.\n')
    sections.append('\nSecondary prepared-online timing from the complete fixed-N accuracy pass follows. It has one fresh process per point and a different corpus from the seven-repetition primary timing experiment; it does not replace that experiment or establish an eligible frontier speedup.\n\n'+table(acc['summary'],[('workload','Workload'),('backend','Backend'),('mean_ms','Secondary mean ms'),('p99_ms','Secondary p99 ms')]))
    selection=json.loads((ROOT/'evidence/selection_record.json').read_text());agroups,_=read_run(accuracy);tgroups,_=read_run(timing);frontier=[]
    # Familywise alpha fixed before results by three workloads and all planned
    # pair comparisons, including deferred cells. No result-dependent reduction.
    alpha=.05/(len(WORKS)*len(json.loads((accuracy/'config.json').read_text())['backends'])*(len(json.loads((accuracy/'config.json').read_text())['backends'])-1)/2)
    for work in WORKS:
        base=index.get('quality_reference_labels',{}).get(work,'tuned_tesseract');sw='seamwise_selected';a=agroups.get((work,sw));b=agroups.get((work,base))
        f=dict(workload=work,Seamwise=sw,reference=base,quality_margin=.10,status='UNRESOLVED_INCOMPLETE',S_frontier=None,validation_point_qualified=selection['selected'][work]['candidate_meets_validation_point_target'])
        if a and b:
            ar=a[0][1];br=b[0][1];assert [r['sample_id'] for r in ar]==[r['sample_id'] for r in br]
            stat=paired([r['logical_failure'] for r in ar],[r['logical_failure'] for r in br],alpha);f['paired']=stat
            f['status']='QUALITY_NOT_ESTABLISHED' if stat['noninferiority_one_sided_upper']>0 else 'NONINFERIOR_TO_FROZEN_REFERENCE'
            if any(r['service_failure'] for r in ar):f['status']='INELIGIBLE_INVALID_OUTPUT'
            if f['status']=='NONINFERIOR_TO_FROZEN_REFERENCE' and f['validation_point_qualified'] and (work,sw) in tgroups and (work,base) in tgroups:
                aa=np.array([[r['latency_ns'] for r in rr] for j,rr in sorted(tgroups[(work,base)],key=lambda z:z[0]['repetition'])]);bb=np.array([[r['latency_ns'] for r in rr] for j,rr in sorted(tgroups[(work,sw)],key=lambda z:z[0]['repetition'])]);f['S_frontier']=timing_ratio(aa,bb)
                f['claim_scope']='Only frozen reference operating point; deferred external families prevent a universal strongest-native claim'
        frontier.append(f)
    report['frontier']=frontier
    sections.append('\n'+table(frontier,[('workload','Workload'),('status','10% quality gate'),('S_frontier','Eligible reference speed ratio')]))
    sections.append('\nNo overall strongest-native frontier advantage is asserted. Validation used the official optimized Tesseract build, LDPC BP-LSD/BP-OSD, current official Relay-BP, and the official GARI C kernel with a verified task-specific augmentation. Deferred operating points and incomplete tuning trials remain unresolved rather than counted as defeats. A raw latency ratio cannot repair a failed/inconclusive quality gate.\n')
    memory=ROOT/index['memory'];mem=analyze(memory);report['memory']=mem
    sections.append('\n## Memory, tails and execution reliability\n\nThe table separates process baseline, preparation residency, high-water RSS and completed memory audits. The full independent timing corpus has 1,024 shots; allocation requests and independent/repeated-syndrome soaks cover that corpus in separate instrumented passes. This is not a 10,000-shot accuracy-corpus memory claim. Requested allocation bytes are not live bytes; native owned-capacity payloads exclude allocator overhead and some third-party ownership. Memory failures do not erase committed decode results.\n')
    sections.append(table(mem['summary'],[('workload','Workload'),('backend','Backend'),('status','Status'),('baseline_after_library_load_bytes','Baseline RSS bytes'),('after_prepare_rss_bytes','Prepared RSS bytes'),('high_water_process_rss_bytes','High-water RSS bytes'),('memory_audit_available','Full audit available')]))
    memory_details=[]
    for r in mem['summary']:
        p=memory/(r['workload']+'__'+r['backend']+'__r0')/'memory.json'
        if not p.exists():continue
        audit=json.loads(p.read_text());cap=audit.get('native_capacity',{});alloc=audit.get('allocation_counts',[]);soak=[s['rss_bytes'] for s in audit.get('soak',[])]
        memory_details.append(dict(workload=r['workload'],backend=r['backend'],corpus_shots=audit['corpus_shots'],
            prepared_capacity_payload_bytes=cap.get('prepared_capacity_payload_bytes'),workspace_capacity_payload_bytes=sum(s.get('workspace_capacity_payload_bytes',0) for s in cap.get('solvers',[])),
            calling_thread_request_calls=sum(x['calls'] for x in alloc),calling_thread_requested_bytes=sum(x['requested_bytes'] for x in alloc),soak_rss_span_bytes=max(soak)-min(soak) if soak else None))
    report['memory_details']=memory_details
    sections.append('\n'+table(memory_details,[('workload','Workload'),('backend','Backend'),('prepared_capacity_payload_bytes','Prepared owned payload bytes'),('workspace_capacity_payload_bytes','Workspace owned payload bytes'),('calling_thread_request_calls','Requests / corpus'),('calling_thread_requested_bytes','Requested bytes / corpus'),('soak_rss_span_bytes','RSS span across 3 soak checkpoints')]))
    if 'optimization_memory' in index:
        revision_path=ROOT/index['optimization_memory'];revision_ledger=json.loads((revision_path/'execution_ledger.json').read_text())
        report['revision_memory_statuses']=dict(collections.Counter(r['status'] for r in revision_ledger))
        sections.append(f"\nRevision allocation controls on the full 128-ID engineering validation corpus: {report['revision_memory_statuses']}. Their independently instrumented requests, capacities and soak RSS are in `{index['optimization_memory']}/analysis.json`; they are not final latency measurements.\n")
    sections.append('\nThe first final memory run (`20261110T050626Z-memory-5cc48225`) retains nine startup crashes before decoding. Dynamic TLS lookup in the diagnostic malloc hooks was replaced with initial-exec TLS; the known-allocation calibration (3 requests, 140 bytes, 2 explicit frees) and native-extension import pass are retained. This changed only memory instrumentation. The decoder source/binary, frozen policies and samples remained the same for the fresh memory rerun. Counters cover allocation requests on the calling decoder thread and do not report live allocated bytes. Deferred rows marked UNSUPPORTED at the budget-deferral stage do not mean the backend API is unavailable.\n')
    sections.append('\nMean and p99 must be assessed per workload from the timing table; no universal tail or memory improvement is inferred from a mean speedup. No per-shot real-time deadline experiment was run. Bulk job timeouts, missing outputs and logical miscorrections have different meanings.\n')
    validation=json.loads((ROOT/index['validation']/'execution_ledger.json').read_text());report['validation_statuses']=dict(collections.Counter(j['status'] for j in validation))
    sections.append(f"\n## Validation, scaling and remaining comparisons\n\nValidation ledger: {report['validation_statuses']}. All 36 method-ablation jobs completed on the same 64 validation IDs per workload, spanning joint/cut/halo/repair with HUF reference, BP-assisted reference and official native LSD families. All 63 initial implementation-control jobs and the additional rebuild-fairness controls completed. See their raw analysis and per-shot files.\n")
    sections.append('\nThe 28 validation DECODE_TIMEOUT ledger entries comprise seven actual decode timeouts and 21 trials not launched after the 1,800-second stage cap. Their stage labels distinguish these cases; unlaunched trials are not measured baseline defeats.\n')
    method=json.loads((ROOT/index['method_ablation']/'analysis.json').read_text());method_groups=collections.defaultdict(dict)
    for r in method['summary']:method_groups[(r['workload'],r['config']['family'])][r['config']['policy']]=r
    method_rows=[]
    for (work,family),points in sorted(method_groups.items()):
        row=dict(workload=work,family=family)
        for policy in ['joint','cut','halo1','repair1']:row[policy]=points[policy]['failures']
        row['joint_mean_ms']=points['joint']['mean_ms'];row['repair_mean_ms']=points['repair1']['mean_ms'];method_rows.append(row)
    report['method_ablation_descriptive']=method_rows
    sections.append('\nSame-family method ablation: each failure count has denominator 64 validation circuit shots; timing is one process and exploratory. HUF/BPHUF are reference variants, LSD is the verified native LDPC family. Different policy outputs do not qualify as exact implementation optimizations. This small cohort does not establish an independent-test advantage.\n\n'+table(method_rows,[('workload','Workload'),('family','Local family'),('joint','Joint failures'),('cut','Cut failures'),('halo1','Halo1 failures'),('repair1','Repair1 failures'),('joint_mean_ms','Joint mean ms'),('repair_mean_ms','Repair1 mean ms')]))
    if 'scaling' in index:
        p=ROOT/index['scaling'];status=p/'scaling_results.json'
        if status.exists():sections.append('\nScaling measurements and actual N_det/N_fault/incidence/depth/gate counts are in '+index['scaling']+'/scaling_results.json. These are 16-shot exploratory controls, not threshold evidence. Large proportional-depth stress workloads are explicitly deferred.\n')
    sections.append(f"\nHistorical audit: {len(original)} original files unchanged; {report['historical_regression']['exact_executions']} correction-identical stored-shot executions across {report['historical_regression']['statuses'].get('PASS',0)} available groups. Missing historical outputs remain unavailable. The old primary BP-assisted point still has 29/256 logical failures in both modes. Reused historical executions add zero independent accuracy samples.\n")
    profile_rows=[]
    for p in json.loads((ROOT/index['profiles']/'profile_summary.json').read_text()):
        counts=p['solver_counts'];bp=sum(s['bp_ns'] for s in counts);outer=sum(p['wrapper'][k] for k in ['cut_ns','repair_ns','frame_ns'])
        profile_rows.append(dict(workload=p['model'],mode='persistent' if p['persistent'] else 'rebuild',shots=p['shots'],bp_fraction=bp/outer if outer else None,
            insertions=sum(s['insertions'] for s in counts),roots=sum(s['roots'] for s in counts),terminal_ms=sum(s['terminal_ns'] for s in counts)/1e6,
            other_work_elimination_bound=outer/bp if bp else None))
    report['current_native_profile']=profile_rows
    sections.append('\n## Measured limiting work\n\nSeparate 32-shot validation diagnostic passes retain stage intervals and native gprof call graphs. BP remains the dominant measured work. Fractions below use the sum of native cut/repair/frame wrapper intervals; they exclude Python binding and instrumentation overhead outside those intervals. Nested local stages cannot be added again to wrapper totals.\n\n'+table(profile_rows,[('workload','Workload'),('mode','Mode'),('bp_fraction','BP fraction of wrapper intervals'),('insertions','Insertion calls / 32 shots'),('roots','Root queries / 32 shots'),('terminal_ms','Terminal ms / 32 shots'),('other_work_elimination_bound','Ideal bound if all non-BP work vanished')]))
    sections.append('\nThese are wrapper-only Amdahl bounds for this diagnostic cohort with BP held fixed; they are not full binding/API bounds or performance forecasts. In particular, the small measured terminal-solve fraction cannot explain a further 2x-5x whole-path gain. New BP/local-solver/repair policies would require a separately frozen accuracy evaluation.\n')
    sections.append('\nThe canonical terminal solve remains in production. Oracle-only canonical-basis investigations, if present, are not native speed claims. Packed terminal, prior revisions, stage/gprof profiles, operation counts and cluster distributions are retained independently. Neither feasible witnesses nor cost descent prove maximum likelihood or the correct logical class.\n')
    investigation=json.loads((ROOT/'evidence/terminal_canonical_investigation.json').read_text());report['terminal_investigation']=investigation
    sections.append(f"\nThe finite canonical-basis exchange oracle passed {investigation['finite_systems']} systems. Naive activation-order witnesses differed from the frozen canonical correction in {investigation['naive_working_witness_differs_from_canonical']} cases; exchanges reproduced it in the tested consistent cases. This is an investigation, not a native integrated optimization or a proof of minimum-likelihood decoding.\n")
    accounting=json.loads((ROOT/'evidence/compute_accounting.json').read_text());report['compute_accounting']=accounting
    sections.append(f"\nCompleted primary timing, fixed-N accuracy and successful memory workers used {accounting['primary_known_worker_cpu_hours']:.3f} CPU hours against the predeclared four-hour confirmatory cap. Builds, exploratory controls, gprof and postprocessing have separate budgets/scopes; this is not a four-hour claim for the entire project. See `evidence/compute_accounting.json` for stage records and the failed memory-startup wall cost.\n")
    sections.append('\nReconstructed final non-singleton component CDFs, merge-weighted CDFs, per-circuit-shot maxima, terminal rank lists and difficult-shot diagnostic strata are retained under the current profile run (`*_final_components.json`, `*_component_weighted_cdf.png`, `*_runtime_clusters.png`). Aggregate local histories cannot identify every component with its individual circuit shot; that missing map is explicitly labeled, while per-shot maxima and failed-call counts are preserved. Native gprof latency and separate audit-pass sizes provide an explanatory association, not a release-latency fit or near-linearity claim.\n')
    sections.append('\n## Reproduction and remaining work\n\n[README.md](README.md) gives the build and frozen-run commands; [audit.md](audit.md) records adapter/provenance limits. The run-to-artifact mapping is [evidence/run_index.json](evidence/run_index.json). Additional lifecycle estimates, amortization crossover, p99 hierarchical intervals, exact revision controls, current native profiles, scaling plots and validation-only mean-latency-budget envelopes are in evidence/ and the indexed runs. Validation envelopes use 1/10/100/1000 ms mean budgets and are descriptive; they do not establish test-set superiority or per-shot deadline reliability.\n\nExact deferred continuation commands and validation-throughput CPU-hour estimates are in [REMAINING.md](REMAINING.md). Nonconvergent Relay/GARI points require a new validation gate before publication timing; their uncompleted tuning grid cannot be counted as a loss. The final source/data/results archive is `artifacts/seamwise_native_research_20261109.tar.gz`, with member integrity hashes and a sibling archive SHA256. Environment caches and VCS object databases are excluded; original source/data/manuscript files are included unchanged.\n')
    (ROOT/'RESULTS.md').write_text('\n\n'.join(sections)+'\n')
    atomic(ROOT/'evidence/final_report.json',report)
    counts_zh='；'.join(f"{w} 为 {selected_counts.get(w,'未完成')} 对 {reference_counts.get(w,'未完成')}" for w in WORKS)
    memo=f"""# 决策备忘录\n\n同策略原生移植在三项工作负载、128 个验证输入和三轮新进程的工程对照中，几何平均加速为重建 {port_r['geometric_mean']:.2f} 倍、持久 {port_p['geometric_mean']:.2f} 倍，纠错向量逐项一致。原生持久化相对共享优化前端的重建模式，独立 1,024 输入、七轮计时的几何平均比为 {persist['geometric_mean']:.3f} 倍。两种贡献分别报告。\n\n独立准确率按预先固定的每点 10,000 shots 执行。选定 Seamwise 与冻结 Tesseract 的逻辑失败数：{counts_zh}。三个点均未建立 10% 相对非劣性，没有 S_frontier 资格，不能宣称质量匹配或全面领先最强原生解码器。配对差异、置信区间及多重校正见 RESULTS.md 和 evidence/final_report.json。\n\nTesseract 使用含 2026 优化的官方 release 源码；Relay 使用修复逐次解码 RNG 状态的官方提交；LSD/OSD 使用官方 LDPC。GARI 的联合模型和逻辑映射已验证并实际运行，但非收敛与预算耗尽完整保留。原作者 HUF 可执行实现本次仍不可用，参考实现不冒称原版。\n\n历史数据和论文未改写。零错误、小样本、固定深度扫描以及批作业超时，均不构成阈值、精确相同准确率或实时可靠性结论。后续优先补齐声明延期的强基线与稀有错误统计，不应从 Python 加速直接写出研究优势。\n"""
    (ROOT/'DECISION_MEMO_ZH.md').write_text(memo)
    print(ROOT/'RESULTS.md')

if __name__=='__main__':main()
