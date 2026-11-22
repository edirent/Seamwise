"""Postprocess all frozen outcomes; never select policies or amend the lock."""
import sys,pathlib,json,itertools,collections,math,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from analysis import read_run
from freeze_guard import verify_lock
from seamwise_bench.analysis import cp_lower,cp_upper,timing_ratio
lock=verify_lock();index=json.loads((ROOT/'results/P4_run_index.json').read_text())
assert index['status'] in ['COMPLETE','ERROR'],'Wait for the entire frozen execution, including timing and memory'
assert sha(ROOT/'configs/confirmatory_lock.json')==index['lock_sha256']
# Recover an interrupted phase without editing its original supervisor journal.
resolved_runs=dict(index['runs'])
for phase in ['primary','secondary','timing','memory']:
 if phase not in resolved_runs:
  candidates=list((ROOT/'results'/('P4_'+phase)).glob('*/EXECUTION_LEDGER.json'))
  assert len(candidates)<=1,'Ambiguous interrupted phase'
  if candidates:resolved_runs[phase]=str(candidates[0].parent.relative_to(ROOT))
alpha=.05/(2*lock['planned_comparisons']);points=[];incomplete=[];phase_points={};raw_ledgers={}
for phase,rel in resolved_runs.items():
 path=ROOT/rel;raw_ledgers[phase]=json.loads((path/'EXECUTION_LEDGER.json').read_text())
 if phase=='memory':continue
 ps,missing=read_run(path);phase_points[phase]=ps
 if phase in ['primary','secondary']:points+=ps;incomplete+=missing
for phase in ['primary','secondary','timing','memory']:
 expected=[];reps=lock['timing_repetitions'] if phase=='timing' else 1;count=lock[phase+'_count']
 done={(j['workload'],j['config']['name'],j['repetition']) for j in raw_ledgers.get(phase,[])}
 for w,configs in lock[phase+'_configs'].items():
  for cfg in configs:
   for rep in range(reps):
    if (w,cfg['name'],rep) not in done:expected.append(dict(workload=w,config=cfg,repetition=rep,count=count,completed=0,missing=count,status='NOT_LAUNCHED_SUPERVISOR_STOP',phase=phase))
 if expected:
  raw_ledgers.setdefault(phase,[]).extend(expected)
  if phase in ['primary','secondary']:incomplete.extend(expected)
for p in points:
 if p['failures']==0:p['wilson95'][0]=0.
 if p['failures']==p['n']:p['wilson95'][1]=1.
by={w:{p['name']:p for p in points if p['workload']==w} for w in WORKS}
def slim(p):return {k:v for k,v in p.items() if k!='rows'}
def comparison(work,A,B):
 a=by[work].get(A);b=by[work].get(B)
 if a is None or b is None:return dict(workload=work,A=A,B=B,status='NOT_EVALUABLE_MISSING_COMPLETE_JOB')
 n=min(a['n'],b['n']);ar=[r for r in a['rows'] if r['shot']<n];br=[r for r in b['rows'] if r['shot']<n]
 assert len(ar)==len(br)==n and [r['sample_id'] for r in ar]==[r['sample_id'] for r in br]
 aa=[r['logical_failure'] for r in ar];bb=[r['logical_failure'] for r in br];p=paired(aa,bb,alpha);c=p['cells'];tail=alpha/6;lower=cp_lower(c['only_A_wrong'],n,tail)-1.1*cp_upper(c['only_B_wrong'],n,tail)-.1*cp_upper(c['both_wrong'],n,tail)
 p['noninferiority_one_sided_upper']=cp_upper(c['only_A_wrong'],n,tail)-1.1*cp_lower(c['only_B_wrong'],n,tail)-.1*cp_lower(c['both_wrong'],n,tail);p['noninferiority_bound_alpha']=alpha/2;p['noninferiority']='PASS' if p['noninferiority_one_sided_upper']<=0 else 'INCONCLUSIVE_OR_INELIGIBLE'
 p['noninferiority_one_sided_lower']=lower;p['noninferiority_decision']='PASS' if p['noninferiority_one_sided_upper']<=0 else 'VIOLATION_DEMONSTRATED' if lower>0 else 'NOT_ESTABLISHED'
 p['superiority']='A_LOWER_FAILURE_RISK' if p['risk_difference_interval'][1]<0 else 'B_LOWER_FAILURE_RISK' if p['risk_difference_interval'][0]>0 else 'NOT_ESTABLISHED'
 if a['invalid'] or b['invalid']:p['noninferiority_decision']='INELIGIBLE_INVALID_CORRECTION';p['superiority']='INELIGIBLE_INVALID_CORRECTION'
 p['noninferiority']=p['noninferiority_decision']
 # Same semantic configuration under two role names must reproduce exact outputs.
 ca={k:v for k,v in a['config'].items() if k!='name'};cb={k:v for k,v in b['config'].items() if k!='name'}
 if ca==cb:assert [(r['prediction'],r['correction_sha256']) for r in ar]==[(r['prediction'],r['correction_sha256']) for r in br]
 return dict(workload=work,A=A,B=B,status='COMPLETE',n=n,paired=p,multiplicity_comparisons=lock['planned_comparisons'],subset_rule='fixed shared shot indices 0..min(N_A,N_B)-1; declared 2000-ID component prefix')
comparisons=[comparison(w,A,B) for w in WORKS for A,B in itertools.combinations(sorted(by[w],key=lambda name:(name!='selected_combined',name)),2)]
primary_comparisons=[]
for w in WORKS:
 for ref in ['original','baseline_tesseract']:
  primary_comparisons.append(comparison(w,'selected_combined',ref))
 ref=lock['selection'][w]['reference']
 if ref!='baseline_tesseract':primary_comparisons.append(comparison(w,'selected_combined',ref))
# A retry is an interruption recovery, never an opportunity to choose a favorable result.
recovery_path=ROOT/'evidence/P4_recovery_plan.json';recovery=json.loads(recovery_path.read_text()) if recovery_path.exists() else None
if recovery:
 checks=[]
 for attempt in recovery['interrupted_attempts']:
  path=ROOT/attempt['path'];assert sha(path)==attempt['sha256'];job=json.loads((path.parent/'job.json').read_text());p=by[job['workload']].get(job['config']['name'])
  if p is None:checks.append(dict(path=attempt['path'],status='NOT_EVALUABLE_RETRY_INCOMPLETE'));continue
  lookup={r['sample_id']:r for r in p['rows']};oldrows=[json.loads(line) for line in path.read_text().splitlines()]
  exact=all((r['prediction'],r['correction_sha256'],r['logical_failure'])==(lookup[r['sample_id']]['prediction'],lookup[r['sample_id']]['correction_sha256'],lookup[r['sample_id']]['logical_failure']) for r in oldrows)
  checks.append(dict(path=attempt['path'],status='PASS' if exact else 'FAIL',duplicate_ids_checked=len(oldrows),duplicates_increase_accuracy_N=False));assert exact,'Interrupted attempt differs from fixed-configuration retry'
 atomic(ROOT/'evidence/recovery_prediction_crosscheck.json',checks)
accuracy=dict(status='COMPLETE' if not incomplete and index['status']=='COMPLETE' else 'PARTIAL',primary_fixed_n=lock['primary_count'],secondary_fixed_n=lock['secondary_count'],planned_comparisons=lock['planned_comparisons'],familywise_alpha=.05,endpoint_families=2,per_comparison_alpha=alpha,summary=[slim(p) for p in points],primary_comparisons=primary_comparisons,comparisons=comparisons,incomplete_jobs=incomplete,scope='new frozen independent circuit samples; repetitions never increase independent N')
atomic(ROOT/'results/accuracy_analysis.json',accuracy)
lines=['# Independent accuracy results','','Policy/source/data lock: `configs/confirmatory_lock.json`, SHA256 `'+index['lock_sha256']+'`. Choices and fixed counts precede each job’s `truth_access.json`. The new circuit-generated confirmatory stream has '+str(lock['primary_count'])+' fixed primary IDs and '+str(lock['secondary_count'])+' fixed shared component IDs per workload. Previous 10,000-shot tests and all 512 new validation shots are exploratory. Sampled errors/true observables are absent from the decoder API; labels are read only for external scoring after the lock.','','No policy was selected using these outcomes. The internal validation rule chooses the fastest finalist within 10% of the minimum Seamwise validation failure count; it is not an external noninferiority test. Tesseract was the strongest eligible full-validation reference on all three workloads. Official native LSD/OSD and available eligible Relay are separate component comparisons. GARI’s invalid validation outcome and other uncompleted/ineligible prior operating points are preserved, not called defeated. Their new inferential comparisons are NOT_EVALUABLE. See the execution ledger and P2 evidence.','','## Fixed primary matrix','','Wilson intervals below are marginal 95%, not multiplicity-adjusted. “Invalid” counts an explicitly available correction failing D x=s. Tesseract supplies a logical frame only, so its correction validity is UNAVAILABLE; zero reported invalid frames is not a certificate for an unreturned correction. Native/official adapter correction-frame consistency is checked outside timing, and new production decoders also enforce full syndrome consistency internally.','','| Workload | Configuration | Failures / N | Wilson 95% (%) | Invalid / corrections checked |','|---|---|---:|---|---:|']
for p in phase_points.get('primary',[]):
 lo,hi=p['wilson95'];checked=sum(r['correction_validity'] is not None for r in p['rows']);validity=str(p['invalid'])+' / '+str(checked) if checked else 'UNAVAILABLE (frame only)';lines.append(f"| {p['workload']} | {p['name']} | {p['failures']}/{p['n']} | {lo*100:.4g}–{hi*100:.4g} | {validity} |")
lines+=['','## Paired primary conclusions','','A is the selected improved Seamwise and B is the named comparator. Cell order: both correct / only A wrong / only B wrong / both wrong. The paired risk difference is p_A−p_B. Confidence bounds use simultaneous exact binomial bounds on multinomial cells and a union bound, without treating the cells as independent. Multiplicity is fixed at '+str(lock['planned_comparisons'])+' planned pairwise comparisons across the complete primary+component matrix, including missing jobs. A further factor of two covers risk-difference and noninferiority endpoints jointly; each NI bound uses half its endpoint alpha (six exact cell tails). Per-endpoint alpha='+f'{alpha:.8g}'+'. It is never reduced after outcomes.','','Noninferiority uses p_A−1.10 p_B≤0 with the previously declared 10% relative margin. PASS requires its adjusted one-sided upper bound≤0. A positive adjusted lower bound demonstrates violation; otherwise it is NOT_ESTABLISHED. Zero/zero observed failures has no finite risk-ratio estimate and cannot establish this relative criterion under these bounds. Marginal Wilson overlap is not used to infer superiority.','','| Workload | B | Paired cells | Risk difference (%) | Adjusted CI (%) | NI contrast upper (%) | 10% NI decision |','|---|---|---|---:|---|---:|---|']
for c in primary_comparisons:
 if c['status']!='COMPLETE':lines.append(f"| {c['workload']} | {c['B']} | NOT_EVALUABLE | — | — | — | Missing complete job |");continue
 p=c['paired'];z=p['cells'];lo,hi=p['risk_difference_interval'];cells='/'.join(str(z[k]) for k in ['both_correct','only_A_wrong','only_B_wrong','both_wrong']);lines.append(f"| {c['workload']} | {c['B']} | {cells} | {100*p['risk_difference']:.4g} | {100*lo:.4g}–{100*hi:.4g} | {100*p['noninferiority_one_sided_upper']:.4g} | {p['noninferiority_decision']} |")
lines+=['','## Fixed 2000-ID component and external comparisons','','These roles were selected before new test labels opened. Their N differs from the primary matrix. Pairwise comparisons to a primary configuration use the predeclared shared 0..1999 prefix, never a favorable intersection or a latency-selected subset. Full paired cells and adjusted intervals for every available planned pair are in `accuracy_analysis.json`.','','| Workload | Component | Failures / N | Wilson 95% (%) | Invalid | Auxiliary single-pass mean ms |','|---|---|---:|---|---:|---:|']
for p in phase_points.get('secondary',[]):
 lo,hi=p['wilson95'];lines.append(f"| {p['workload']} | {p['name']} | {p['failures']}/{p['n']} | {100*lo:.4g}–{100*hi:.4g} | {p['invalid']} | {p['mean_ms']:.4g} |")
lines+=['','## Precision, missing outcomes and limits','','The maximum 10,000 new samples were generated before tuning. The validation-only five-hour throughput rule fixed N='+str(lock['primary_count'])+' before any confirmatory label access. Rare-event comparisons, especially BB144, can remain inconclusive at this N. For every zero-failure cell the one-sided marginal 95% upper bound is 1−0.05^(1/N); zero failures does not establish zero risk. No timeout/unsupported/service failure is counted as a correct shot or a defeated baseline. Incomplete prefixes are retained but excluded from completed failure rates; missing counts are explicit in raw ledgers. Correction validity unavailable from a frame-only baseline remains unavailable. No additional confirmatory claim is made from timing or memory repetitions.']
for p in phase_points.get('primary',[]):
 if p['failures']==0:lines.append(f"- {p['workload']} / {p['name']}: 0/{p['n']}, marginal one-sided 95% risk upper {100*cp_upper(0,p['n'],.05):.5g}%.")
lines+=['',f"Incomplete accuracy jobs: {len(incomplete)}. Complete primary jobs: {len(phase_points.get('primary',[]))}. Complete secondary jobs: {len(phase_points.get('secondary',[]))}. Raw files and failures are retained under the phase paths in `P4_run_index.json`.",'','The bounded oracle and candidate search establish positive witnesses, not exhaustive causal classification. Model equivalence gates exclude no untested defect. Native HUF is the reference-compatible reimplementation from the original framework; it is not falsely labeled the original author executable. Tesseract/Relay/LDPC/GARI source and binary provenance remain in the sealed original framework and every new job summary.']
if incomplete:
 lines+=['','| Workload | Job | Runtime status | Completed | Missing |','|---|---|---|---:|---:|']
 for j in incomplete:lines.append(f"| {j['workload']} | {j['config']['name']} | {j['status']} | {j.get('completed',0)} | {j.get('missing',j['count']-j.get('completed',0))} |")
(ROOT/'results/ACCURACY_RESULTS.md').write_text('\n'.join(lines)+'\n')
# Separate dedicated timing corpus. Repetitions are process blocks, not new accuracy N.
timing=[];timing_raw=collections.defaultdict(list)
for p in phase_points.get('timing',[]):timing_raw[p['workload'],p['name']].append(p)
for (w,name),ps in timing_raw.items():
 ps.sort(key=lambda q:q['repetition']);expected=list(range(lock['timing_repetitions']))
 if [p['repetition'] for p in ps]!=expected:continue
 ids=[r['sample_id'] for r in ps[0]['rows']]
 for p in ps:assert [r['sample_id'] for r in p['rows']]==ids
 t=np.array([[r['latency_ns'] for r in p['rows']] for p in ps])/1e6
 timing.append(dict(workload=w,name=name,independent_ids=lock['timing_count'],repetitions=len(ps),mean_ms=float(t.mean()),median_ms=float(np.median(t)),p95_ms=float(np.quantile(t,.95)),p99_ms=float(np.quantile(t,.99)),maximum_ms=float(t.max()),repetition_mean_ms=t.mean(axis=1).tolist(),repetition_p99_ms=np.quantile(t,.99,axis=1).tolist(),preparation_ms=[p['preparation_ms'] for p in ps]))
ratios=[]
for w in WORKS:
 a=timing_raw.get((w,'selected_combined'));b=timing_raw.get((w,'original'))
 if a and b and len(a)==len(b)==lock['timing_repetitions']:
  aa=np.array([[r['latency_ns'] for r in p['rows']] for p in sorted(a,key=lambda p:p['repetition'])]);bb=np.array([[r['latency_ns'] for r in p['rows']] for p in sorted(b,key=lambda p:p['repetition'])]);ratios.append(dict(workload=w,selected_over_original=timing_ratio(aa,bb)))
memory=[]
for j in raw_ledgers.get('memory',[]):
 path=pathlib.Path(j['directory']) if j.get('directory') else None;file=path/'memory.json' if path else None;audit=json.loads(file.read_text()) if file and file.exists() else None
 memory.append(dict(workload=j['workload'],name=j['config']['name'],status=j['status'],baseline_rss_bytes=j.get('baseline_rss_bytes'),prepared_rss_bytes=j.get('prepared_rss_bytes'),audit=audit,scope='separate instrumented full validation corpus; never used for publication latency'))
atomic(ROOT/'results/latency_memory_analysis.json',dict(timing=timing,paired_timing_ratios=ratios,memory=memory,incomplete_timing_jobs=[j for j in raw_ledgers.get('timing',[]) if j['status']!='COMPLETE']))
lines=['# Prepared-online latency and memory','','Primary publication timing uses the independent 1024-ID timing corpus, three fresh processes per configuration, one pinned core (CPU0 on this host), one decoder thread and batch1. Backend order is randomized and saved, with identical per-repetition shot permutations. Warmup uses the same 16 validation syndromes. The clock covers prepared input detector bits through returned logical frame, including Python/native interface and intrinsic decoder work; it excludes model/data loading, preparation, external validity/truth scoring, JSON journals and diagnostics. Source/binary/dependency fingerprints are verified for every phase. No decoder/build/profiler benchmark was run concurrently with these sequential timing workers.','','The original native binary is unchanged. Memory instrumentation runs in separate fresh workers with explicit instrumented scope. Accuracy-corpus single-pass timings remain auxiliary, never substituted for missing dedicated timing measurements. Tesseract enters dedicated timing only on workloads that met the frozen validation point-estimate 10% screen (BB144); that screen is not the independent noninferiority test. Its d3/d5 auxiliary timings are retained without an accuracy-qualified speed claim.','','| Workload | Decoder | Mean ms | Median ms | p95 ms | p99 ms | Maximum ms |','|---|---|---:|---:|---:|---:|---:|']
for t in timing:lines.append('| '+t['workload']+' | '+t['name']+' | '+' | '.join(f"{t[k]:.6g}" for k in ['mean_ms','median_ms','p95_ms','p99_ms','maximum_ms'])+' |')
lines+=['','| Workload | Selected/original mean ratio | Pointwise 95% paired hierarchical bootstrap |','|---|---:|---|']
for r in ratios:
 d=r['selected_over_original'];lo,hi=d['interval'];lines.append(f"| {r['workload']} | {d['ratio']:.4g} | {lo:.4g}–{hi:.4g} |")
lines+=['','Ratios use shared sample IDs and resample process blocks plus independent shot IDs (600 bootstrap draws). They describe timing variability for this host, not an accuracy test or a production deadline guarantee. Full process means, p99s, preparation times and maxima are in `latency_memory_analysis.json`. Severe tail or mean regressions remain visible. Fixed K≤16, depth≤2, ≤128 cached moves, and ≤2 conditional solver calls bound added search; the implementation does not hide uncontrolled/exhaustive search in timing. Initialization/fallback BP calls are additional and explicitly outside the repair-call cap.','','## Separate memory and soak','','Each original/selected pair uses all 512 validation IDs, followed by two cycles of the full independent corpus and 512 repetitions of one fixed syndrome per cycle: 2560 total decode calls per process including the initial 512-ID pass. This stresses reset/reuse but is not a long-duration stability guarantee. Resident pages include interpreter, imported libraries, samples and allocator arenas; RSS changes are not exact decoder ownership. Native capacity values count the implemented owned payload categories, not every allocator or object header. The candidate dense payload is a lower estimate, not a measured peak total. Joint-policy preparation retains duplicated conditional storage and is reported as implemented.','','The unchanged calibrated glibc interposer counts calling-thread allocation requests during each full-corpus decode; it does not count every Python allocator event or report live bytes. Instrumentation overhead is excluded from all publication latency.','','| Workload | Decoder | Status | Baseline RSS MiB | Prepared RSS MiB | HWM MiB | Owned prepared/workspace payload MiB | Requests/call (mean) | Requested KiB/call (mean) | Soak RSS MiB |','|---|---|---|---:|---:|---:|---|---:|---:|---|']
for m in memory:
 a=m['audit'] or {};cap=a.get('native_capacity',{});alloc=a.get('allocation_counts',[]);fmt=lambda x:'—' if x is None else f'{x/2**20:.4g}';payload='/'.join(fmt(cap.get(k)) for k in ['prepared_capacity_payload_bytes','workspace_capacity_payload_bytes']);calls='—' if not alloc else f"{np.mean([x['calls'] for x in alloc]):.4g}";requested='—' if not alloc else f"{np.mean([x['requested_bytes'] for x in alloc])/1024:.4g}";soak='/'.join(fmt(q['rss_bytes']) for q in a.get('soak',[]));lines.append(f"| {m['workload']} | {m['name']} | {m['status']} | {fmt(m['baseline_rss_bytes'])} | {fmt(m['prepared_rss_bytes'])} | {fmt(a.get('high_water_rss_bytes'))} | {payload} | {calls} | {requested} | {soak} |")
lines+=['','## Uninstrumented primary-worker resident memory','','These are fresh accuracy workers on the full fixed primary corpus, not decoder-owned allocation totals and not the separate 512-ID instrumented soak. The interrupted Tesseract attempt is excluded; the complete fixed-N retry is used. Interpreter, data and library residency are included. For an accuracy-only checkpoint continuation, whole-cohort high-water RSS is UNAVAILABLE; resume-process RSS is preserved separately in its raw summary.','','| Workload | Decoder | Baseline / prepared / high-water RSS MiB |','|---|---|---|']
for q in phase_points.get('primary',[]):
 values='/'.join(('UNAVAILABLE' if q[k] is None else f"{q[k]/2**20:.5g}") for k in ['baseline_rss_bytes','prepared_rss_bytes','high_water_rss_bytes']);lines.append(f"| {q['workload']} | {q['name']} | {values} |")
lines+=['','Full memory raw allocation requests, independent/repeated cycle sizes, candidate payload lower estimates and RSS checkpoints are retained per worker. A small number of soak checkpoints cannot establish the absence of slow leaks. Any failed audit is labeled separately and cannot invalidate an already atomically committed decode journal.','','## Computation budget','','Frozen forecast: '+f"{lock['forecast_s']/3600:.4g}"+' hours; maximum '+f"{lock['max_wall_s']/3600:.4g}"+' wall hours (a conservative cap for sequential one-core CPU work). Supervisor elapsed: '+f"{index.get('elapsed_s',0)/3600:.4g}"+' hours. Per-stage paths/statuses, missing counts and parent-watchdog events are in `P4_run_index.json` and the execution ledger. Completed jobs were retained; an interrupted job was retried with the same fixed configuration and IDs as documented below, without outcome-based selection.']
(ROOT/'results/LATENCY_RESULTS.md').write_text('\n'.join(lines)+'\n')
# Frontier plot: distinguish dedicated timing and auxiliary one-pass measurements.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axs=plt.subplots(1,3,figsize=(16,5));colors={'original':'#777777','selected_combined':'#147d64','baseline_tesseract':'#8b368c'}
for ax,w in zip(axs,WORKS):
 for name in ['original','selected_combined','baseline_tesseract']:
  p=by[w].get(name)
  if p is None:continue
  ts=[t for t in timing if t['workload']==w and t['name']==name];dedicated=bool(ts);x=ts[0]['mean_ms'] if ts else p['mean_ms'];lo,hi=p['wilson95'];label=name.replace('_',' ')+(' (accuracy-run time)' if not dedicated else '')
  ax.errorbar(x,100*p['failure_rate'],yerr=[[max(0.,100*(p['failure_rate']-lo))],[max(0.,100*(hi-p['failure_rate']))]],fmt='o' if dedicated else 'x',capsize=3,color=colors[name],label=label)
 for name,p in by[w].items():
  if name in colors:continue
  ax.scatter(p['mean_ms'],100*p['failure_rate'],s=12,color='#bbbbbb',alpha=.6)
 if w.startswith('bb'):
  inset=ax.inset_axes([.07,.39,.49,.43])
  for name in ['original','selected_combined','baseline_tesseract']:
   p=by[w].get(name)
   if p is None:continue
   ts=[t for t in timing if t['workload']==w and t['name']==name];x=ts[0]['mean_ms'] if ts else p['mean_ms'];lo,hi=p['wilson95'];inset.errorbar(x,100*p['failure_rate'],yerr=[[max(0.,100*(p['failure_rate']-lo))],[max(0.,100*(hi-p['failure_rate']))]],fmt='o',capsize=2,color=colors[name])
  inset.set(xscale='log',ylim=(-.015,.65),title='Primary rare-event detail');inset.tick_params(labelsize=7);inset.title.set_fontsize(8);inset.grid(alpha=.2)
 ax.set(xscale='log',xlabel='Prepared-online mean latency (ms)',ylabel='Logical failure probability (%)',title=w.replace('_B4',''));ax.set_ylim(bottom=-.01);ax.grid(alpha=.2);ax.legend(fontsize=7)
fig.suptitle('Frozen independent test: accuracy–latency trade-off (no accuracy-qualified speedup implied)',fontsize=12);fig.text(.5,.01,'Primary error bars: 8000-ID Wilson95. Gray points: 2000-ID components, auxiliary accuracy-run timing. No exact population frontier is certified.',ha='center',fontsize=8);fig.tight_layout(rect=(0,.05,1,.95));fig.savefig(ROOT/'results/PARETO_FRONTIER.png',dpi=180);plt.close(fig)
# Master job ledger retains all stages and expected failures/deferrals.
stage_file=ROOT/'results/STAGE_EXECUTION_LEDGER.json';stage_events=json.loads((stage_file if stage_file.exists() else ROOT/'results/EXECUTION_LEDGER.json').read_text());atomic(stage_file,stage_events);job_runs=[]
for file in sorted((ROOT/'results').glob('*/*/EXECUTION_LEDGER.json')):
 rows=json.loads(file.read_text());job_runs.append(dict(run=str(file.parent.relative_to(ROOT)),jobs=rows))
followup_records=[dict(path=name,status='COMPLETE',sha256=sha(ROOT/name)) for name in ['results/BP_quality_summary.json','results/failure_attribution/20261110T085943Z/finite_LLR_summary.json','results/failure_attribution/20261110T085943Z/final_attribution_estimates.json'] if (ROOT/name).exists()]
master=dict(status='COMPLETE' if index['status']=='COMPLETE' and all(j['status']=='COMPLETE' for jobs in raw_ledgers.values() for j in jobs) else 'COMPLETED_WITH_GAPS',stage_events=stage_events,job_runs=job_runs,diagnostic_followups=followup_records,reporting_recovery=dict(prior_failure='evidence/finish_pipeline.failed.json',current_status='evidence/finish_pipeline.json',reason='Mathematical zero-event Wilson endpoint normalized; negative roundoff in plotting distances clamped only for display'),P4_expanded_ledgers=raw_ledgers,historical_interrupted_attempts=recovery['interrupted_attempts'] if recovery else [],confirmatory=index,lock_sha256=index['lock_sha256'],reporting='All completed, timed-out, unsupported, failed, and intentionally failing orchestration-smoke jobs retained. No incomplete job counted as defeated. Stage events also refer to raw P0/P1 oracle/conditional logs, including bounded optimization statuses.')
atomic(ROOT/'results/MASTER_EXECUTION_LEDGER.json',master);atomic(ROOT/'results/EXECUTION_LEDGER.json',master)
# Produce a compact Chinese decision using frozen results and explicit component contrasts.
zh=['# Seamwise 逻辑失败研究结论','','本次完成归因、条件局部求解比较、BP 与候选/半径策略实现，以及新独立样本上的固定配置检验。成功标准是可复现的证据与诚实的准确率—计算代价结论，不预设必须达到 Tesseract 水平。原始论文实验、旧结果及旧解码器未改动。','','## Q1：可证实的失败比例','','旧测试已降为探索数据。84 个分层诊断样本的 native trace 与归档解码器逐位一致，其中 d3/d5 各含16个失败、BB含12个失败。P0/P1阶段生产半径下，便宜正确候选的搜索不足证据为6/16、2/16、0/12；全部测试后，对固定选定配置回放原84个诊断样本，合并正见证增至7/16、4/16、12/12；不可达为2/16、0/16、0/12；按生成候选的仿射基点修正后，正确逻辑方向未在增长支撑中暴露为14/16、13/16、7/12。类别可重叠，未暴露不等于证明它是唯一原因，也不证明存在便宜的正确候选。最终搜索见证的分层加权比例为44.9%、27.8%、100.0%，探索性点位95%有限总体区间分别为15.2%–81.7%、6.9%–68.1%、78.6%–100.0%；阶段记录及最终交集见 `failure_attribution/FINAL_ATTRIBUTION.md`。未找到见证不是不存在正确低成本解的证明。没有拿到证明所有正确解都无法下降的 ACCEPTANCE_LIMITED 最优性证书；这不是证明成本规则从未受限。','','## Q2：主要限制是什么','','证据支持多种并存限制：有直接的搜索不足证书；多数失败样本缺少增长支撑中的目标逻辑方向；d5/BB有正确候选因成本被拒绝，BB还出现便宜但逻辑错误的更新破坏正确初值。成本与逻辑正确性不一致得到逐样本证实，但精确逻辑类后验与全局最优性未被解决。BB的固定配置回放已为12/12旧失败给出更便宜的正确全带解，因此这些样本在形式定义上都不是ACCEPTANCE_LIMITED。匹配的32个验证输入上，原BP即使增加到60次迭代仍为0/32收敛；尺度0.8、60次上限不加阻尼为7/32收敛，加阻尼后为32/32收敛、平均5.09次迭代。d3也观察到阻尼改善，但d5的硬残差降低并未保证更好的逻辑结果。详见 `BP_QUALITY.md`。这支持BB上的推断/候选排序限制，不能把BP认定为所有工作负载的唯一主因。固定外部变量与搜索/选择的影响应按对照分别判断。未发现模型/数值不一致，但检查范围有限。','','## Q3：新独立测试中的改善','','以下配置完全由512个验证样本选定，再固定测试样本数及五小时预算。主比较使用相同的'+str(lock['primary_count'])+'个新独立电路样本；多重比较校正固定为'+str(lock['planned_comparisons'])+'组。','']
for w in WORKS:
 a=by[w].get('selected_combined');b=by[w].get('original');t=by[w].get('baseline_tesseract')
 if not a or not b or not t:zh.append('- '+w+'：主比较存在缺失，不能评价。');continue
 c=comparison(w,'selected_combined','original')['paired'];red=None if not b['failures'] else 100*(1-a['failures']/b['failures']);desc='无法定义' if red is None else f'{red:.1f}%';zh.append(f"- {w}：原版 {b['failures']}/{b['n']} → 选定版 {a['failures']}/{a['n']}，观察到的相对失败数下降 {desc}；Tesseract {t['failures']}/{t['n']}。配对校正结论：{c['superiority']}。零失败不代表真实风险为零。")
improvements=[]
for w in WORKS:
 a=by[w].get('selected_combined');b=by[w].get('original')
 if a and b:improvements.append((b['failure_rate']-a['failure_rate'],w))
if improvements:
 delta,w=max(improvements);zh.append('主配置相对原版观察到的最大绝对风险下降位于 '+w+'，下降 '+f'{100*delta:.4g}'+' 个百分点。这是对冻结配置的描述，不据此重新选择测试配置。')
trajectory_index=ROOT/'results/failure_attribution/current_run.json';trajectory_path=ROOT/json.loads(trajectory_index.read_text())['path']/'trajectory_selection_estimates.json' if trajectory_index.exists() else None
if trajectory_path is not None and trajectory_path.exists():
 trajectory=json.loads(trajectory_path.read_text());note='实际原版生产路径另有以下选择冲突：'+ '；'.join(v['workload']+' '+str(v['selection_failure_union'])+'/'+str(v['n'])+'（正确候选被拒'+str(v['correct_proposal_rejected'])+'，正确初值被错误更新破坏'+str(v['correct_incumbent_harmed'])+'）' for v in trajectory)+'。BB按分层加权为58.3%，点位95%有限总体区间33.3%–81.0%。这与最终状态条件查询的计数范围不同，不应混为同一张表，也不是所有正确解均被成本规则阻挡的最优性证明。详见 failure_attribution/TRAJECTORY_SELECTION.md。'
 # Place the clarification immediately before Q2, so Q1 retains its causal scope.
 position=zh.index('## Q2：主要限制是什么');zh[position:position]=[note,'']
zh+=['','## Q4：延迟与内存代价','']
for w in WORKS:
 a=next((t for t in timing if t['workload']==w and t['name']=='selected_combined'),None);b=next((t for t in timing if t['workload']==w and t['name']=='original'),None)
 if a and b:zh.append(f"- {w}：独立计时均值 {b['mean_ms']:.4g} → {a['mean_ms']:.4g} ms；p99 {b['p99_ms']:.4g} → {a['p99_ms']:.4g} ms。")
memory_parts=[]
for work in WORKS:
 pair={m['name']:m['audit'] for m in memory if m['workload']==work and m['audit']}
 if all(name in pair for name in ['original','selected_combined']):memory_parts.append(work+' '+f"{pair['original']['high_water_rss_bytes']/2**20:.4g}→{pair['selected_combined']['high_water_rss_bytes']/2**20:.4g} MiB")
memory_paragraph='独立512-ID内存浸泡的进程高水位RSS：'+'；'.join(memory_parts)+'。RSS含解释器、样本和分配器；调用分配请求不是同时存活内存，观测值不是所有输入的内存上界。'
zh+=['','均值、尾延迟、最大值及独立内存/分配/浸泡结果均在 `LATENCY_RESULTS.md`。候选预算固定，不隐藏无界搜索；表中如有显著 p99 回退，则准确率收益需要承担该代价。RSS包含解释器/样本/分配器，容量负载不是完整总内存。',memory_paragraph,'','## Q5：是否满足 Tesseract 的10%约束','']
for w in WORKS:
 c=comparison(w,'selected_combined','baseline_tesseract')
 zh.append('- '+w+'：'+(c['paired']['noninferiority_decision'] if c['status']=='COMPLETE' else 'NOT_EVALUABLE')+'。')
zh+=['','不以边际区间重叠推断优劣，不把双零误当相对非劣证明；未通过校正的非劣门槛就不宣称获得“准确率匹配的速度优势”。','','## Q6：收益来自修复结构还是更强内层','', '固定2000个共享测试ID的对照如下；完整配对区间在 `accuracy_analysis.json`。更换内层、BP参数、半径、候选与初值的作用不能混成同一个结构性收益。','','| 工作负载 | 对照 | 失败数/N |','|---|---|---:|']
for w in WORKS:
 for name in ['selected_combined','same_BP_fixed_radius','same_BP_radius2','same_BP_joint','matched_cut','matched_joint','stronger_solver','strong_joint','strong_cut','strong_all_repair']:
  p=by[w].get(name)
  if p:
   rr=[r for r in p['rows'] if r['shot']<lock['secondary_count']];zh.append(f"| {w} | {name} | {sum(r['logical_failure'] for r in rr)}/{len(rr)} |")
zh+=['','### 相同输入的部件配对证据','','下表A−B为风险差，区间已按预定比较矩阵及两类终点保守校正；负值支持A更好。未建立差异不等于证明相同。','','| 工作负载 | A 对 B | 风险差及校正区间（百分点） | 结论 |','|---|---|---|---|']
for w in WORKS:
 for A,B in [('selected_combined','same_BP_fixed_radius'),('selected_combined','same_BP_joint'),('selected_combined','matched_cut'),('strong_all_repair','strong_joint')]:
  c=comparison(w,A,B)
  if c['status']!='COMPLETE':continue
  q=c['paired'];lo,hi=q['risk_difference_interval'];zh.append(f"| {w} | {A} / {B} | {100*q['risk_difference']:.4g} [{100*lo:.4g}, {100*hi:.4g}] | {q['superiority']} |")
# Descriptive comparison of predeclared roles on the identical component prefix.
zh+=['','在同一2000-ID前缀上，d3的选定K2策略与相同BP的单候选策略均为43次失败，增加候选没有展示独立准确率收益；BB选定版本身只改变BP配置，外层结构和严格成本规则保持原样。d5相对同BP切分控制的改善得到校正确认，但相对同BP联合/固定半径控制尚未建立优势。BB的统一OSD0修复控制相对统一OSD0联合控制得到校正后的收益证据，这只说明该内层设置中的修复作用，不能推广为优于最佳联合解码器。']
zh+=['','预定角色在相同2000-ID前缀上的最低观察失败数如下，仅作描述，不据此更换冻结主配置或宣称统计最优：','','| 工作负载 | 观察最低的预定新策略角色（允许并列） | 失败/2000 |','|---|---|---:|']
for w in WORKS:
 roles=['best_bp','stronger_solver','multi_candidate','adaptive_radius','selected_combined','same_BP_fixed_radius'];scores={}
 for name in roles:
  p=by[w].get(name)
  if p:scores[name]=sum(r['logical_failure'] for r in p['rows'] if r['shot']<lock['secondary_count'])
 if scores:
  minimum=min(scores.values());names=', '.join(k for k,v in scores.items() if v==minimum);zh.append(f"| {w} | {names} | {minimum} |")
zh+=['','其他角色之间的差异未因观察排名就自动被认定为显著；完整配对区间及运行代价保留在结果文件中。']
zh+=['','如果选定版相对相同BP固定半径没有经校正的优势，则不能把其相对旧版的收益归因于增加候选。如果相对相同BP联合解码没有经校正的优势，则不能宣称修复结构优于匹配的联合控制。切分到修复的改善仅证明修复能补救该切分初值，并不自动证明它优于全局联合求解。']
zh+=['','固定半径增加K的验证结果为阴性；逻辑类截断质量选择也没有展示足以选为主策略的优势。最终选中的三项均保留原严格成本下降规则。是否能归因于外层修复，应看相同BP、相同求解器、切分/联合/修复的配对差异；相对旧版的改善本身不能证明修复结构优于更强联合解码。没有对其他距离、物理错误率、硬件或长期运行作外推。','','所有完整/部分/失败/超时/不支持及人为失败的流程自检记录保存在 `MASTER_EXECUTION_LEDGER.json`；原始阶段账本未覆盖。可重现入口见上级 `README.md`。']
(ROOT/'results/RESEARCH_DECISION_ZH.md').write_text('\n'.join(zh)+'\n')
if recovery:
 note=('Execution recovery: three complete primary jobs were retained from the initial execution. The interrupted 3188-ID Tesseract prefix remains unchanged and is excluded as an independent estimate; the exact same configuration was retried on all fixed 8000 IDs. If a later stage watchdog left another incomplete Tesseract attempt, the budget-only completion rule can continue its remaining fixed IDs in a fresh process after exact checkpoint replay checks; this retains one unique result per ID and is excluded from dedicated timing. Duplicate predictions were crosschecked and never increase N. An estimated 46.6 minutes of prior active execution are charged to the five-hour planning cap; the offline interruption is excluded. The old worker termination time and uncommitted in-flight work were not recorded, so this is accounted active time with a 30-second allowance, not a certified upper bound on all historical CPU work. The resumed supervisor itself enforces its remaining wall cap. Configuration/source/binary/data locks did not change. Accuracy-run timings across execution dates are auxiliary; dedicated timing is measured entirely in fresh paired workers after recovery. See evidence/P4_recovery_plan.json and recovery_prediction_crosscheck.json.')
 for filename in ['ACCURACY_RESULTS.md','LATENCY_RESULTS.md','RESEARCH_DECISION_ZH.md']:
  p=ROOT/'results'/filename;p.write_text(p.read_text()+'\n\n'+note+'\n')
for filename in ['ACCURACY_RESULTS.md','RESEARCH_DECISION_ZH.md']:
 p=ROOT/'results'/filename;p.write_text(p.read_text()+'\n\nMechanistic follow-up (exploratory, no policy changes): failure_attribution/FINAL_ATTRIBUTION.md combines positive cost witnesses from P0/P1 and the fixed selected-policy replay. BP_QUALITY.md compares all eight predeclared BP presets on identical validation syndromes. These diagnostics do not add confirmatory samples.\n')
# Keep the requested Chinese decision concise; retain full tables in an appendix.
long_decision=ROOT/'results/RESEARCH_DECISION_ZH.md'
(ROOT/'results/RESEARCH_APPENDIX_ZH.md').write_text(long_decision.read_text())
brief=['# Seamwise 研究结论','','完整原始证据、失败尝试和复现入口见 [README](../README.md)；详细配对表见 [附录](RESEARCH_APPENDIX_ZH.md)。所有主配置在新测试标签打开前冻结。','','## Q1：哪些失败原因有直接证据？','','固定配置回放后，原始生产半径中的更便宜正确类见证合计为 d3 **7/16**、d5 **4/16**、BB **12/12**。按历史失败分层加权，比例为44.9%、27.8%、100.0%，探索性点位95%有限总体区间为15.2%–81.7%、6.9%–68.1%、78.6%–100.0%。未找到见证不是不存在解的证明。','','原增长支撑未暴露目标逻辑方向的样本为14/16、13/16、7/12；带内不可达为2/16、0/16、0/12。实际选择冲突为0/16、3/16、7/12；BB其中5个正确初值被错误修复破坏，2个正确候选被拒。这些类别重叠，不能加总成互斥原因。BB全部12个失败存在更便宜正确解，因此它们并非“成本下降必然阻止所有正确解”的ACCEPTANCE_LIMITED。见 [最终归因](failure_attribution/FINAL_ATTRIBUTION.md)。','','## Q2：主要限制是什么？','','BB最强的证据指向BP推断/候选排序：匹配的32个验证综合征中，原BP即使增至60次迭代仍为0/32收敛；尺度0.8、60次上限时，不加阻尼为7/32，加阻尼为32/32，平均5.09次迭代。旧失败上的便宜正确候选进一步证明原搜索遗漏。504个条件问题的原BP LLR与官方实现逐值一致，实际NaN为0，故这些检查不支持移植数值错误的解释。','','d3也支持BP配置改善；d5的硬残差改善没有保证更好的逻辑结果，局部性、搜索与类选择仍存在未解决问题。未证明单一普遍原因，也未证明截断类质量是精确MAP。见 [BP对照](BP_QUALITY.md)。','','## Q3：新独立测试改善多少？','','每项固定8000个独立电路样本。配对区间按425个预定比较和两类终点保守校正。','','| 工作负载 | 原版失败 | 选定版失败 | Tesseract失败 | 相对原版观察下降 | 校正后改善成立？ |','|---|---:|---:|---:|---:|---|']
for work in WORKS:
 a=by[work].get('selected_combined');b=by[work].get('original');t=by[work].get('baseline_tesseract')
 if not all([a,b,t]):continue
 c=comparison(work,'selected_combined','original')['paired'];reduction='不适用' if not b['failures'] else f"{100*(1-a['failures']/b['failures']):.1f}%";decision='是' if c['superiority']=='A_LOWER_FAILURE_RISK' else '未建立';brief.append(f"| {work.split('_p')[0]} | {b['failures']} | {a['failures']} | {t['failures']} | {reduction} | {decision} |")
brief+=['','最明确的独立收益是d3的BP配置组合，保留原分区和成本规则。d5/BB的点估计改善未通过本次保守校正，不能把“未建立”解释为“证明无效”。未按测试排名更换主配置。Wilson区间、全部配对单元及无效/服务失败见 [准确率结果](ACCURACY_RESULTS.md)。','','## Q4：代价是什么？','','以下为独立1024-ID计时集、三个新进程重复、单核单线程batch1；内存为另行512-ID插桩浸泡。','','| 工作负载 | 均值ms：原版→选定 | p99 ms：原版→选定 | 进程高水位MiB：原版→选定 |','|---|---|---|---|']
for work in WORKS:
 a=next((t for t in timing if t['workload']==work and t['name']=='selected_combined'),None);b=next((t for t in timing if t['workload']==work and t['name']=='original'),None);m={v['name']:v['audit'] for v in memory if v['workload']==work and v['audit']}
 if a and b and all(k in m for k in ['original','selected_combined']):brief.append(f"| {work.split('_p')[0]} | {b['mean_ms']:.4g}→{a['mean_ms']:.4g} | {b['p99_ms']:.4g}→{a['p99_ms']:.4g} | {m['original']['high_water_rss_bytes']/2**20:.4g}→{m['selected_combined']['high_water_rss_bytes']/2**20:.4g} |")
brief+=['','d3/d5有明显延迟回退；d5还增加约25 MiB进程高水位。搜索有固定K、深度和调用上限，但不能把有限预算等同于生产时限保证。RSS包含解释器、样本与分配器；分配请求量不是存活内存。见 [延迟与内存](LATENCY_RESULTS.md)。','','## Q5：满足Tesseract的10%相对非劣约束吗？','']
for work in WORKS:
 c=comparison(work,'selected_combined','baseline_tesseract');decision=c.get('paired',{}).get('noninferiority_decision','NOT_EVALUABLE');brief.append('- '+work.split('_p')[0]+'：'+{'NOT_ESTABLISHED':'未建立','VIOLATION_DEMONSTRATED':'约束违反得到统计确认','PASS':'通过'}.get(decision,decision)+'。')
brief+=['','没有工作负载获得通过证明，因此不宣称准确率匹配的速度优势。BB仍是稀有事件，1比0不能视为相对非劣证明。','','## Q6：来自外层修复，还是内层替换？','','相同2000-ID前缀上，d3的K2与相同BP单候选均43次失败，额外候选未显示独立收益；BB选定版本身仅改变BP配置。d5选定版206次，对同BP切分控制353次的改善得到校正确认；对同BP联合226次、固定半径262次尚未建立优势。','','BB的统一OSD0修复100次、联合168次，支持该匹配内层设置中的修复收益；不能推广为优于最佳联合解码。固定半径增K和截断类质量策略未展示足以选入主配置的收益。当前证据支持具体工作负载的BP改善与部分修复作用，不支持普遍的架构优势。']
if recovery:brief+=['','中断前缀3188和后续7319个记录均保留；续跑重放检查与重叠预测核对通过，每个最终样本只计一次。最终79项任务完成。计入先前执行的规划用时约'+f"{index['elapsed_s']/3600:.3g}"+'小时；旧进程丢失的在途工作不可测，不能据此认证全部历史CPU时间的严格上界。详见 [账本](EXECUTION_LEDGER.json)。']
long_decision.write_text('\n'.join(brief)+'\n')

if lock['status'].startswith('REPRODUCTION'):
 for filename in ['ACCURACY_RESULTS.md','LATENCY_RESULTS.md','RESEARCH_DECISION_ZH.md']:
  p=ROOT/'results'/filename;p.write_text('REPRODUCTION ON PREVIOUSLY INSPECTED SAMPLES; NOT NEW CONFIRMATORY EVIDENCE.\n\n'+p.read_text())
print(json.dumps(dict(status=accuracy['status'],primary=[dict(workload=c['workload'],B=c['B'],paired=c.get('paired')) for c in primary_comparisons],timing=timing),indent=2))
