"""Resume an interrupted campaign without editing frozen decoders or inflating N.
Completed full jobs are reused. Incomplete attempts remain immutable and are
replayed in full by the ORIGINAL frozen worker. Only active execution time counts
against the original five-hour budget; the offline interruption is excluded.
"""
import sys,pathlib,json,time,datetime,shutil
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from freeze_guard import verify_lock
from runner import run
pin();lock=verify_lock();indexpath=ROOT/'results/P4_run_index.json';old=json.loads(indexpath.read_text())
assert old['status']=='RUNNING' and old['active_phase']=='primary' and not old['runs']
planpath=ROOT/'evidence/P4_recovery_plan.json'
if planpath.exists():raise RuntimeError('A recovery already exists; inspect it instead of replaying completed attempts')
oldrun=ROOT/'results/P4_primary/20261110T105459Z';oldledger=json.loads((oldrun/'EXECUTION_LEDGER.json').read_text());completed=[j for j in oldledger if j['status']=='COMPLETE'];partials=[]
for f in oldrun.glob('*/shots.jsonl.partial'):
 rows=[json.loads(s) for s in f.read_text().splitlines()];job=json.loads((f.parent/'job.json').read_text());ids=np.random.default_rng(job['permutation_seed']).permutation(job['count']);assert [r['shot'] for r in rows]==ids[:len(rows)].tolist()
 partials.append(dict(path=str(f.relative_to(ROOT)),sha256=sha(f),completed=len(rows),requested=job['count'],mtime_epoch=f.stat().st_mtime,decode_seconds=sum(r['latency_ns'] for r in rows)/1e9,status='INTERRUPTED_ATTEMPT_EXCLUDED_FROM_FINAL_ESTIMATE'))
started=datetime.datetime.fromisoformat(old['started_utc'].replace('Z','+00:00')).timestamp();last=max([p['mtime_epoch'] for p in partials]+[started]);prior_s=max(last-started,sum(j.get('wall_s',0) for j in completed)+sum(p['decode_seconds'] for p in partials))+30
plan=dict(created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),lock_sha256=sha(ROOT/'configs/confirmatory_lock.json'),original_supervisor=old,original_run=str(oldrun.relative_to(ROOT)),prior_active_wall_s_upper_estimate=prior_s,inactive_interval_excluded=True,completed_jobs_reused=len(completed),interrupted_attempts=partials,strategy='fresh full fixed-N retry with unchanged frozen worker; no incomplete prefix used as a completed rate and no duplicate IDs inflate independent N',frozen_decoder_source_unchanged=True)
atomic(planpath,plan);atomic(ROOT/'evidence/P4_run_index.interrupted.json',old);atomic(ROOT/'evidence/P4_recovery_script_sha256.json',dict(path='scripts/recover_confirmatory.py',sha256=sha(__file__)))
index=dict(old,status='RUNNING',resumed_utc=plan['created_utc'],prior_active_wall_s=prior_s,recovery_plan=str(planpath.relative_to(ROOT)));atomic(indexpath,index);start=time.monotonic()
def elapsed():return prior_s+time.monotonic()-start
try:
 for phase in ['primary','secondary','timing','memory']:
  verify_lock();remaining=lock['max_wall_s']-elapsed();f=lock['forecast_components'];reserve={'primary':f['secondary_s']+f['timing_s']+f['memory_s']+60,'secondary':f['timing_s']+f['memory_s']+30,'timing':f['memory_s']+15,'memory':0}[phase];cap=max(.001,remaining-reserve)
  index.update(active_phase=phase,remaining_at_phase_start_s=remaining,phase_cap_s=cap,elapsed_s=elapsed());atomic(indexpath,index)
  configs=lock[phase+'_configs']
  if phase=='primary':
   done={(j['workload'],j['config']['name']) for j in completed};configs={w:[c for c in cs if (w,c['name']) not in done] for w,cs in configs.items()}
  if phase in ['primary','secondary']:count=lock[phase+'_count'];split='confirmatory';reps=1;mode='accuracy'
  elif phase=='timing':count=lock['timing_count'];split='timing';reps=lock['timing_repetitions'];mode='timing'
  else:count=lock['memory_count'];split='validation';reps=1;mode='memory'
  print('PHASE',phase,'count',count,'cap_s',cap,'cumulative_active_s',elapsed(),flush=True)
  path=run(configs,'P4_'+phase+'_recovery' if phase=='primary' else 'P4_'+phase,count,split,reps,cap,cap,mode)
  if phase=='primary':
   joined=ROOT/'results/P4_primary_combined'/time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());joined.mkdir(parents=True,exist_ok=False);jobs=completed+json.loads((path/'EXECUTION_LEDGER.json').read_text());atomic(joined/'EXECUTION_LEDGER.json',jobs);atomic(joined/'planned_configs.json',lock['primary_configs']);atomic(joined/'run.json',dict(status='COMPLETE' if all(j['status']=='COMPLETE' for j in jobs) else 'PARTIAL',count=count,split=split,repetitions=1,mode=mode,recovery=dict(plan=str(planpath.relative_to(ROOT)),new_attempt_run=str(path.relative_to(ROOT)),original_completed_run=str(oldrun.relative_to(ROOT))),elapsed_active_s=elapsed()));atomic(joined/'schedule_segments.json',dict(original_completed=[(j['workload'],j['repetition'],j['config']) for j in completed],retry=json.loads((path/'schedule.json').read_text())));path=joined
  index['runs'][phase]=str(path.relative_to(ROOT));index['elapsed_s']=elapsed();atomic(indexpath,index)
 index.update(status='COMPLETE',elapsed_s=elapsed(),resumed_elapsed_s=time.monotonic()-start,finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()));atomic(indexpath,index);ledger('P4 interrupted execution recovery','COMPLETE',**{k:v for k,v in index.items() if k!='status'})
except Exception as exc:
 import traceback
 index.update(status='ERROR',error=repr(exc),traceback=traceback.format_exc(),elapsed_s=elapsed());atomic(indexpath,index);raise
