"""Execute the frozen matrix sequentially within the predeclared five-hour cap."""
import sys,pathlib,json,time,traceback
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from freeze_guard import verify_lock
from runner import run
pin();lock=verify_lock();index_path=ROOT/'results/P4_run_index.json'
if index_path.exists():raise RuntimeError('Refusing to restart or overwrite a P4 execution')
start=time.monotonic();index=dict(started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),lock_sha256=sha(ROOT/'configs/confirmatory_lock.json'),max_wall_s=lock['max_wall_s'],status='RUNNING',runs={});atomic(index_path,index)
try:
 for phase in ['primary','secondary','timing','memory']:
  verify_lock();remaining=lock['max_wall_s']-(time.monotonic()-start);f=lock['forecast_components']
  reserve={'primary':f['secondary_s']+f['timing_s']+f['memory_s']+60,'secondary':f['timing_s']+f['memory_s']+30,'timing':f['memory_s']+15,'memory':0}[phase]
  cap=max(.001,remaining-reserve)
  index['active_phase']=phase;index['remaining_at_phase_start_s']=remaining;index['phase_cap_s']=cap;atomic(index_path,index)
  if phase in ['primary','secondary']:
   split='confirmatory';count=lock[phase+'_count'];repetitions=1;mode='accuracy'
  elif phase=='timing':split='timing';count=lock['timing_count'];repetitions=lock['timing_repetitions'];mode='timing'
  else:split='validation';count=lock['memory_count'];repetitions=1;mode='memory'
  print('PHASE',phase,'count',count,'cap_s',cap,flush=True)
  path=run(lock[phase+'_configs'],'P4_'+phase,count,split,repetitions,cap,cap,mode)
  index['runs'][phase]=str(path.relative_to(ROOT));index['elapsed_s']=time.monotonic()-start;atomic(index_path,index)
 index.update(status='COMPLETE',elapsed_s=time.monotonic()-start,finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()));atomic(index_path,index)
 ledger('P4 frozen matrix supervisor','COMPLETE',**{k:v for k,v in index.items() if k!='status'})
except Exception as exc:
 index.update(status='ERROR',error=repr(exc),traceback=traceback.format_exc(),elapsed_s=time.monotonic()-start);atomic(index_path,index);raise
