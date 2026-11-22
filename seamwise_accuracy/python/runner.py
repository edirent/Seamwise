"""Fresh sequential workers; truth is confined to external post-decode scoring."""
import os,sys,json,pathlib,time,traceback,subprocess,resource,hashlib
import numpy as np
from common import *

def factory(a,cfg,audit=False):
 kind=cfg.get('kind','new')
 if kind!='new':
  c=dict(cfg)
  if kind=='original':c['kind']='native'
  return make(a,c,audit=audit)
 import _accuracy_native
 p=a['p']
 if cfg.get('candidate'):
  options=dict(cfg,audit=audit);moves={}
  if cfg.get('joint'):options.update(radius=2,adaptive=False)
  else:options.setdefault('radius',int(cfg.get('policy','repair1')[-1]))
  if cfg.get('K',1)>1:
   radii=[1,2] if options.get('adaptive') else [options['radius']]
   manifest=json.loads((ROOT/'results/prepared_pools/manifest.json').read_text())
   for radius in radii:
    path=ROOT/'results/prepared_pools'/(a['path'].name+'_r'+str(radius)+'.json');assert sha(path)==manifest['files'][str(path.relative_to(ROOT))];pooldata=json.loads(path.read_text());assert pooldata['model_hash']==DATA['workloads'][a['path'].name]['model_hash'];moves[radius]=[b['moves'] for b in pooldata['bands']]
  obj=_accuracy_native.AccuracyDecoder(a['d'].shape[0],supports(a['d']),supports(a['l']),p.tolist(),np.log((1-p)/p).tolist(),a['labels'].tolist(),a['meta']['blocks'],options,moves);obj.observable_count=a['l'].shape[0];return obj
 obj=_accuracy_native.Decoder(a['d'].shape[0],supports(a['d']),supports(a['l']),p.tolist(),np.log((1-p)/p).tolist(),a['labels'].tolist(),a['meta']['blocks'],cfg.get('family','bphuf'),True,cfg.get('policy','repair1'),audit,cfg.get('iterations',30),cfg.get('order',0),False);obj.observable_count=a['l'].shape[0]
 if cfg.get('band_family'):obj.set_band_solver(cfg['band_family'],cfg.get('band_iterations',60),cfg.get('band_order',2))
 obj.configure_bp(cfg.get('scale',.625),cfg.get('damping',0),cfg.get('schedule','parallel')=='serial')
 return obj

def rss():
 import psutil
 return psutil.Process().memory_info().rss

def worker(path):
 pin();job=json.loads(pathlib.Path(path).read_text());dest=pathlib.Path(job['directory']);cfg=job['config'];start=time.monotonic();summary=dict(job,status='ERROR',completed=0,scope='instrumented_full_corpus_memory_not_publication_latency' if job['mode']=='memory' else 'prepared_online_detector_bits_to_observable_frame_batch1',threads=1,cpu=min(os.sched_getaffinity(0)),batch=1)
 try:
  lock=None
  if job['split']=='confirmatory' or (ROOT/'configs/confirmatory_lock.json').exists() and job['mode'] in ['timing','memory']:
   from freeze_guard import verify_job
   lock=verify_job(job)
  if job['split']=='confirmatory':
   atomic(dest/'truth_access.json',dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),lock_sha256=sha(ROOT/'configs/confirmatory_lock.json'),requested_count=job['count']))
  manifest=json.loads((ROOT/'results/new_samples/manifest.json').read_text());item=manifest['workloads'][job['workload']];sp=item['splits'][job['split']];assert sha(ROOT/sp['path'])==sp['sha256'];a=model(job['workload'])
  with np.load(ROOT/sp['path']) as arrays:raw=dict(detectors=arrays['detectors'],observables=arrays['observables'])
  warm=np.load(ROOT/item['splits']['validation']['path'])['detectors'][:16]
  summary.update(model_hash=item['model']['model_hash'],sample_sha256=sp['sha256'],config_sha256=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest(),loadavg_start=os.getloadavg())
  from seamwise_bench.audit import environment
  snapshot=environment();summary['versions']=snapshot['versions'];summary['binary_sha256']=snapshot['binary_sha256'];summary['provenance_commits']=snapshot['commits']
  if lock is not None:
   for key in ['versions','binary_sha256','commits']:
    assert snapshot[key]==lock['runtime_provenance'][key],'Frozen dependency provenance drift: '+key
  kind=cfg.get('kind','new');module={'new':'_accuracy_native','original':'_native','tesseract':'tesseract_decoder','lsd':'ldpc','osd':'ldpc','relay':'relay_bp','gari':'_gari'}[kind];__import__(module);summary['baseline_rss_bytes']=rss()
  if kind in ['new','original']:summary['native_module_sha256']=sha(pathlib.Path(sys.modules[module].__file__))
  atomic(dest/'stage.json',dict(stage='preparation',started=time.monotonic()));t=time.perf_counter_ns();decoder=factory(a,cfg);summary['preparation_ns']=time.perf_counter_ns()-t;summary['prepared_rss_bytes']=rss();atomic(dest/'stage.json',dict(stage='decode',started=time.monotonic()))
  for s in warm:decoder.decode(s)
  ids=np.random.default_rng(job.get('permutation_seed',202611101)).permutation(job['count']);times=[]
  with (dest/'shots.jsonl.partial').open('x') as f:
   for idx in ids:
    s=raw['detectors'][idx];t=time.perf_counter_ns();frame0,x=decoder.decode(s);elapsed=time.perf_counter_ns()-t;frame0=np.asarray(frame0,dtype=np.uint8)
    assert frame0.shape==(a['l'].shape[0],) and np.all(frame0<=1)
    isvalid=None if x is None else valid(a,np.asarray(x),s)
    if x is not None:assert np.array_equal(frame(a,np.asarray(x)),frame0)
    logical=bool(np.any(frame0!=raw['observables'][idx]));r=dict(sample_id=sp['sample_id_prefix']+':'+str(idx),shot=int(idx),latency_ns=elapsed,logical_failure=logical,invalid=isvalid is False,correction_validity=isvalid,prediction=frame0.tolist(),correction_sha256=None if x is None else hashlib.sha256(np.asarray(x,dtype=np.uint8).tobytes()).hexdigest())
    if hasattr(decoder,'stats'):
     r['native_work']=dict(decoder.stats())
     if cfg.get('selection','cost')=='cost':assert r['native_work']['higher_cost_updates']==0
    f.write(json.dumps(r,separators=(',',':'))+'\n');f.flush();times.append(elapsed);summary['completed']+=1
    if isvalid is False and not (job['mode']=='validation' and kind in ['relay','gari']):raise RuntimeError('CORRECTNESS_GATE_INVALID')
  os.replace(dest/'shots.jsonl.partial',dest/'shots.jsonl');summary.update(status='COMPLETE',latency_ns=dict(mean=float(np.mean(times)),median=float(np.median(times)),p95=float(np.quantile(times,.95)),p99=float(np.quantile(times,.99)),maximum=max(times)),high_water_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,wall_s=time.monotonic()-start,process_cpu_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime)
  atomic(dest/'decode_summary.json',summary)
  if job['mode']=='memory':
   from memory_audit import audit_memory
   summary['stage']='memory';summary['scope']='instrumented_full_corpus_memory_not_publication_latency';atomic(dest/'stage.json',dict(stage='memory',started=time.monotonic()))
   audit=audit_memory(decoder,raw['detectors'],ids,dest,summary);summary.update(high_water_rss_bytes=audit['high_water_rss_bytes'],wall_s=time.monotonic()-start,process_cpu_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime)
 except Exception as exc:summary.update(status='MEMORY_AUDIT_FAILED' if (dest/'decode_summary.json').exists() and job['mode']=='memory' else 'ERROR',error=repr(exc),traceback=traceback.format_exc(),wall_s=time.monotonic()-start)
 atomic(dest/'summary.json',summary)

def run(configs,name,count=128,split='validation',repetitions=1,wall_cap=1800,point_cap=240,mode='validation'):
 out=ROOT/'results'/name/time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());out.mkdir(parents=True,exist_ok=False);atomic(out/'planned_configs.json',configs);ledger0=[];start=time.monotonic();rng=np.random.default_rng(202611102);schedule=[]
 for work in WORKS:
  for rep in range(repetitions):
   for idx in rng.permutation(len(configs[work])):schedule.append((work,rep,configs[work][int(idx)]))
 atomic(out/'schedule.json',schedule)
 for work,rep,cfg in schedule:
  jid=work+'__'+cfg['name']+'__r'+str(rep);dest=out/jid;dest.mkdir();job=dict(workload=work,config=cfg,count=count,split=split,repetition=rep,mode=mode,directory=str(dest),permutation_seed=202611103+rep)
  atomic(dest/'job.json',job)
  if time.monotonic()-start>=wall_cap:
   result=dict(job,status='DECODE_TIMEOUT',stage='not_launched_stage_cap',completed=0,missing=count)
  elif cfg.get('deferred'):
   result=dict(job,status='UNSUPPORTED',stage='predeclared_work_budget',reason=cfg['deferred'],completed=0,missing=count)
  else:
   with (dest/'worker.log').open('x') as f:
    env=dict(os.environ,ACCURACY_NATIVE_BUILD='build_prod',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',RAYON_NUM_THREADS='1')
    if mode=='memory':env['LD_PRELOAD']=str(OLD/'build/liballoc_audit.so')
    proc=subprocess.Popen([sys.executable,str(ROOT/'python/runner.py'),'--worker',str(dest/'job.json')],stdout=f,stderr=subprocess.STDOUT,env=env)
    launched=time.monotonic()
    while proc.poll() is None:
     if time.monotonic()-launched>point_cap or time.monotonic()-start>wall_cap:proc.kill();proc.wait();break
     try:proc.wait(timeout=.2)
     except subprocess.TimeoutExpired:pass
   if (dest/'summary.json').exists():result=json.loads((dest/'summary.json').read_text())
   else:
    prefix=dest/'shots.jsonl.partial';completed=sum(1 for _ in prefix.open()) if prefix.exists() else 0
    committed=dest/'decode_summary.json'
    result=json.loads(committed.read_text()) if committed.exists() else dict(job,completed=completed,missing=count-completed)
    result.update(status='MEMORY_AUDIT_FAILED' if committed.exists() and mode=='memory' else 'DECODE_TIMEOUT' if proc.returncode==-9 else 'ERROR',stage='parent_watchdog_or_crash',exitcode=proc.returncode)
  ledger0.append(result);atomic(out/'EXECUTION_LEDGER.json',ledger0);print(jid,result['status'],str(result.get('completed',0))+'/'+str(count),flush=True)
  if 'CORRECTNESS_GATE_INVALID' in result.get('error',''):raise RuntimeError('Stopped for invalid new/native correction: '+jid)
 atomic(out/'run.json',dict(status='COMPLETE' if all(r['status']=='COMPLETE' for r in ledger0) else 'PARTIAL',mode=mode,count=count,split=split,repetitions=repetitions,elapsed_s=time.monotonic()-start));ledger(name,'COMPLETE' if all(r['status']=='COMPLETE' for r in ledger0) else 'PARTIAL',run=str(out.relative_to(ROOT)),jobs=len(ledger0),elapsed_s=time.monotonic()-start);return out
if __name__=='__main__':worker(sys.argv[2])
