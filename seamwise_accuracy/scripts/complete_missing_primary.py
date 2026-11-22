"""Budget-only completion of unchanged frozen primary points after recovery.
The decision uses completion status, validation throughput and remaining time;
it never reads logical outcomes to choose configurations or sample counts.
"""
import sys,pathlib,json,time,datetime,subprocess
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from freeze_guard import verify_lock
from runner import run
from analysis import read_run
pin();lock=verify_lock();idxpath=ROOT/'results/P4_run_index.json';idx=json.loads(idxpath.read_text());assert idx['status']=='COMPLETE'
recordpath=ROOT/'evidence/P4_primary_completion.json'
if recordpath.exists():raise RuntimeError('Completion already recorded; do not repeat completed attempts')
primary=ROOT/idx['runs']['primary'];original_jobs=json.loads((primary/'EXECUTION_LEDGER.json').read_text());jobs=list(original_jobs);lookup={(j['workload'],j['config']['name']):i for i,j in enumerate(jobs)}
missing=[(w,c) for w in WORKS for name in ['original','selected_combined','baseline_tesseract'] for c in lock['primary_configs'][w] if c['name']==name and jobs[lookup[w,name]]['status']!='COMPLETE']
if not missing:
 atomic(recordpath,dict(status='NOT_NEEDED',all_primary_complete=True,policy_lock_sha256=sha(ROOT/'configs/confirmatory_lock.json')));print('All primary jobs complete; no additional retry');raise SystemExit(0)
finished=datetime.datetime.fromisoformat(idx['finished_utc'].replace('Z','+00:00')).timestamp();charged=idx['elapsed_s']+max(0,time.time()-finished);start=time.monotonic();validation=ROOT/json.loads((ROOT/'results/finalists_current.json').read_text())['path'];points,_=read_run(validation);means={(p['workload'],p['name']):p['mean_ms']/1000 for p in points};attempts=[]
def continue_tesseract(cfg,w,prior,prefix,remaining):
 stamp=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());out=ROOT/'results/P4_primary_completion'/stamp;out.mkdir(parents=True,exist_ok=False);configs={work:([cfg] if work==w else []) for work in WORKS};atomic(out/'planned_configs.json',configs);atomic(out/'schedule.json',[(w,0,cfg)]);dest=out/(w+'__'+cfg['name']+'__r0');dest.mkdir();job=dict(workload=w,config=cfg,count=lock['primary_count'],split='confirmatory',repetition=0,mode='accuracy',directory=str(dest),permutation_seed=prior.get('permutation_seed',202611103),resume_source=str(prefix),resume_source_sha256=sha(prefix));atomic(dest/'job.json',job)
 env=dict(os.environ,ACCURACY_NATIVE_BUILD='build_prod',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',RAYON_NUM_THREADS='1');t=time.monotonic()
 with (dest/'worker.log').open('x') as f:
  proc=subprocess.Popen([sys.executable,str(ROOT/'scripts/resume_tesseract_accuracy.py'),str(dest/'job.json')],stdout=f,stderr=subprocess.STDOUT,env=env)
  try:proc.wait(timeout=max(.001,remaining-2))
  except subprocess.TimeoutExpired:proc.kill();proc.wait()
 if (dest/'summary.json').exists():result=json.loads((dest/'summary.json').read_text())
 else:
  partial=dest/'shots.jsonl.partial';n=sum(1 for _ in partial.open()) if partial.exists() else 0;result=dict(job,status='DECODE_TIMEOUT' if proc.returncode==-9 else 'ERROR',completed=n,missing=job['count']-n,stage='checkpoint_continuation_watchdog',exitcode=proc.returncode)
 atomic(out/'EXECUTION_LEDGER.json',[result]);atomic(out/'run.json',dict(status='COMPLETE' if result['status']=='COMPLETE' else 'PARTIAL',mode='accuracy',count=job['count'],split='confirmatory',repetitions=1,elapsed_s=time.monotonic()-t,checkpoint_continuation=True));return out,result
for w,cfg in missing:
 verify_lock();remaining=lock['max_wall_s']-charged-(time.monotonic()-start);role=lock['selection'][w]['selected_source_role'] if cfg['name']=='selected_combined' else cfg['name'];prior=jobs[lookup[w,cfg['name']]];prefix=pathlib.Path(prior['directory'])/'shots.jsonl.partial';reuse=0
 if cfg['kind']=='tesseract' and prefix.exists():
  from resume_tesseract_accuracy import checked_prefix
  ids=np.random.default_rng(prior.get('permutation_seed',202611103)).permutation(lock['primary_count']);manifest=json.loads((ROOT/'results/new_samples/manifest.json').read_text());reuse=len(checked_prefix(prefix.read_bytes(),ids,manifest['workloads'][w]['splits']['confirmatory']['sample_id_prefix']))
 forecast=1.25*(lock['primary_count']-reuse)*means[w,role]+(60 if reuse else 5)
 if remaining<forecast:
  attempts.append(dict(workload=w,config=cfg,status='NOT_LAUNCHED_REMAINING_BUDGET',remaining_s=remaining,validation_forecast_s=forecast));continue
 if reuse:path,result=continue_tesseract(cfg,w,prior,prefix,remaining)
 else:
  configs={work:([cfg] if work==w else []) for work in WORKS};path=run(configs,'P4_primary_completion',lock['primary_count'],'confirmatory',1,max(.001,remaining-2),max(.001,remaining-2),'accuracy');result=json.loads((path/'EXECUTION_LEDGER.json').read_text())[0]
 attempts.append(dict(workload=w,config=cfg,status=result['status'],run=str(path.relative_to(ROOT)),remaining_at_launch_s=remaining,checkpoint_rows_reused=reuse,checkpoint_resume_worker_sha256=sha(ROOT/'scripts/resume_tesseract_accuracy.py') if reuse else None))
 if result['status']=='COMPLETE':
  prior=jobs[lookup[w,cfg['name']]];prefix=pathlib.Path(prior['directory'])/'shots.jsonl.partial';checks=0
  if prefix.exists():
   new={r['sample_id']:r for r in [json.loads(s) for s in (pathlib.Path(result['directory'])/'shots.jsonl').read_text().splitlines()]}
   if reuse:
    prior_rows=checked_prefix(prefix.read_bytes(),np.random.default_rng(prior.get('permutation_seed',202611103)).permutation(lock['primary_count']),manifest['workloads'][w]['splits']['confirmatory']['sample_id_prefix'])
   else:prior_rows=[json.loads(line) for line in prefix.read_text().splitlines()]
   for r in prior_rows:
    n=new[r['sample_id']];assert (r['prediction'],r['correction_sha256'])==(n['prediction'],n['correction_sha256']),'Retry changed predictions';checks+=1
  attempts[-1]['overlapping_predictions_exact']=checks;jobs[lookup[w,cfg['name']]]=result
 elapsed=charged+time.monotonic()-start
 atomic(recordpath,dict(status='RUNNING',attempts=attempts,accounted_active_s=elapsed,policy_lock_sha256=sha(ROOT/'configs/confirmatory_lock.json')))
joined=ROOT/'results/P4_primary_final'/time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());joined.mkdir(parents=True,exist_ok=False);atomic(joined/'EXECUTION_LEDGER.json',jobs);atomic(joined/'planned_configs.json',lock['primary_configs']);atomic(joined/'run.json',dict(status='COMPLETE' if all(j['status']=='COMPLETE' for j in jobs) else 'PARTIAL',count=lock['primary_count'],split='confirmatory',repetitions=1,mode='accuracy',prior_consolidated_run=str(primary.relative_to(ROOT)),completion_attempts=attempts))
atomic(ROOT/'evidence/P4_index_before_primary_completion.json',idx);idx.update(elapsed_s=charged+time.monotonic()-start,finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()));idx['runs']['primary']=str(joined.relative_to(ROOT));atomic(idxpath,idx);atomic(recordpath,dict(status='COMPLETE',attempts=attempts,accounted_active_s=idx['elapsed_s'],all_primary_complete=all(j['status']=='COMPLETE' for j in jobs),policy_lock_sha256=sha(ROOT/'configs/confirmatory_lock.json')))
ledger('Budget-only completion of interrupted primary points','COMPLETE',record=str(recordpath.relative_to(ROOT)),accounted_active_s=idx['elapsed_s']);print(json.dumps(attempts,indent=2))
