"""Accuracy-only continuation of a fixed Tesseract cohort after watchdog stop.
Frozen production factory, configuration, model, binary and ID permutation are
unchanged. Checkpoints do not create new samples or publication timing runs.
"""
import sys,pathlib,json,time,resource,hashlib,os,traceback
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from runner import factory,rss
from freeze_guard import verify_job

def checked_prefix(data,ids,prefix):
 rows=[];lines=data.splitlines()
 for i,line in enumerate(lines):
  try:r=json.loads(line)
  except ValueError:
   if i==len(lines)-1 and not data.endswith(b'\n'):break
   raise
  assert i<len(ids) and r['shot']==int(ids[i]) and r['sample_id']==prefix+':'+str(int(ids[i]))
  assert not r['invalid'] and r['correction_validity'] is None and r['correction_sha256'] is None
  rows.append(r)
 return rows

def worker(jobfile):
 pin();job=json.loads(pathlib.Path(jobfile).read_text());dest=pathlib.Path(job['directory']);cfg=job['config'];start=time.monotonic();summary=dict(job,status='ERROR',completed=0,scope='prepared_online_detector_bits_to_observable_frame_batch1',threads=1,cpu=min(os.sched_getaffinity(0)),batch=1,resumed_accuracy=True,publication_timing_eligible=False,high_water_rss_bytes=None,resident_memory_scope='resume process only; whole-cohort high water unavailable')
 try:
  assert cfg['kind']=='tesseract' and job['split']=='confirmatory' and job['mode']=='accuracy';lock=verify_job(job)
  from seamwise_bench.audit import environment
  env=environment()
  for key in ['versions','binary_sha256','commits']:assert env[key]==lock['runtime_provenance'][key]
  summary.update(versions=env['versions'],binary_sha256=env['binary_sha256'],provenance_commits=env['commits'])
  manifest=json.loads((ROOT/'results/new_samples/manifest.json').read_text());item=manifest['workloads'][job['workload']];sp=item['splits']['confirmatory'];assert sha(ROOT/sp['path'])==sp['sha256'];a=model(job['workload']);ids=np.random.default_rng(job['permutation_seed']).permutation(job['count']);source=pathlib.Path(job['resume_source']);assert sha(source)==job['resume_source_sha256'];data=source.read_bytes();rows=checked_prefix(data,ids,sp['sample_id_prefix']);summary['completed']=len(rows)
  atomic(dest/'truth_access.json',dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),lock_sha256=sha(ROOT/'configs/confirmatory_lock.json'),requested_count=job['count'],resumed_accuracy=True))
  with np.load(ROOT/sp['path']) as z:det=z['detectors'];obs=z['observables']
  warm=np.load(ROOT/item['splits']['validation']['path'])['detectors'][:16];summary.update(model_hash=item['model']['model_hash'],sample_sha256=sp['sha256'],config_sha256=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest(),baseline_rss_bytes=rss(),loadavg_start=os.getloadavg())
  t=time.perf_counter_ns();decoder=factory(a,cfg);summary['preparation_ns']=time.perf_counter_ns()-t;summary['prepared_rss_bytes']=rss()
  for s in warm:decoder.decode(s)
  # Decoder-visible replay checks: choose IDs by position, never by outcomes.
  for position in np.linspace(0,len(rows)-1,min(16,len(rows)),dtype=int):
   r=rows[int(position)];f,x=decoder.decode(det[r['shot']]);assert x is None and np.array_equal(f,r['prediction']),'Checkpoint replay changed predictions'
  decoder=factory(a,cfg)
  for s in warm:decoder.decode(s)
  times=[r['latency_ns'] for r in rows]
  for r in rows:assert bool(np.any(np.asarray(r['prediction'],dtype=np.uint8)!=obs[r['shot']]))==r['logical_failure']
  atomic(dest/'continuation.json',dict(source=str(source),source_sha256=job['resume_source_sha256'],reused_unique_ids=len(rows),replayed_ids=min(16,len(rows)),new_ids=job['count']-len(rows),independent_N=job['count'],worker_script_sha256=sha(__file__),correction_validity='UNAVAILABLE_FRAME_ONLY',timing='Mixed fresh-process segments, auxiliary accuracy-corpus times only; never dedicated publication timing'))
  with (dest/'shots.jsonl.partial').open('x') as f:
   for r in rows:f.write(json.dumps(r,separators=(',',':'))+'\n')
   f.flush()
   for idx in ids[len(rows):]:
    s=det[idx];t=time.perf_counter_ns();frame0,x=decoder.decode(s);elapsed=time.perf_counter_ns()-t;frame0=np.asarray(frame0,dtype=np.uint8);assert x is None and frame0.shape==(a['l'].shape[0],) and np.all(frame0<=1)
    r=dict(sample_id=sp['sample_id_prefix']+':'+str(int(idx)),shot=int(idx),latency_ns=elapsed,logical_failure=bool(np.any(frame0!=obs[idx])),invalid=False,correction_validity=None,prediction=frame0.tolist(),correction_sha256=None);f.write(json.dumps(r,separators=(',',':'))+'\n');f.flush();times.append(elapsed);summary['completed']+=1
  os.replace(dest/'shots.jsonl.partial',dest/'shots.jsonl');summary.update(status='COMPLETE',latency_ns=dict(mean=float(np.mean(times)),median=float(np.median(times)),p95=float(np.quantile(times,.95)),p99=float(np.quantile(times,.99)),maximum=max(times)),wall_s=time.monotonic()-start,process_cpu_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,resume_process_high_water_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
  atomic(dest/'decode_summary.json',summary)
 except Exception as exc:summary.update(status='ERROR',error=repr(exc),traceback=traceback.format_exc(),wall_s=time.monotonic()-start)
 atomic(dest/'summary.json',summary)
if __name__=='__main__':worker(sys.argv[1])
