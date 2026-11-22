"""Paired circuit pilot. Run --suite or --child MODEL ENGINE COUNT.
All outcomes and measured durations retained. No outcome-selected shots.
"""
import os,sys,json,time,hashlib,resource,threading,subprocess,signal
from pathlib import Path
import numpy as np
from scipy import sparse
HERE=Path(__file__).resolve().parent
DATA=HERE/'data';RESULTS=Path(os.environ.get('SEAMWISE_RESULTS_DIR',str(HERE/'results')));RESULTS.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(HERE/'research'))
import decoders
from huf import HUF

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rss():
    s=Path('/proc/self/status').read_text()
    return int(next(x.split()[1] for x in s.splitlines() if x.startswith('VmRSS:')))*1024
def child(model,engine,count):
    budget=180 if engine in ['BPHUF','BPSW'] and model=='surface_d5_p0.006_B4' else 45
    signal.alarm(budget) # Preallocated full-sample primary BP-oracle comparison.
    path=DATA/model;a=np.load(path/'metadata_arrays.npz')
    d=sparse.load_npz(path/'D.npz');l=sparse.load_npz(path/'L.npz')
    raw=np.load(path/'samples.npz');ss=raw['detectors'][:count].astype(np.uint8);obs=raw['observables'][:count]
    start=time.perf_counter();stats=[];objects=[]
    if engine in ['HUF','SW','BPHUF','BPSW']:
        old=decoders.make_solver
        def factory(matrix,p,unused):
            if engine.startswith('BP'):
                from bp_huf import BPHUF
                h=BPHUF(matrix,p,engine=='BPSW')
            else:h=HUF(matrix,p,engine=='SW')
            objects.append(h);return h
        decoders.make_solver=factory
        stack=decoders.Stack(d,l,a['p'],a['detector_blocks'],json.loads((path/'model.json').read_text())['blocks'],engine)
        stack.prepare(['repair1'])
        fn=lambda s:stack.decode(s,'repair1')[0]
    elif engine=='Tesseract':
        import stim
        from tesseract_decoder import tesseract as te
        cfg=te.TesseractConfig(dem=stim.DetectorErrorModel.from_file(path/'detector_model.dem'),det_beam=5,pqlimit=200000)
        backend=te.TesseractDecoder(cfg)
        fn=lambda s:backend.decode(s.astype(bool))
    elif engine=='Relay':
        import relay_bp
        backend=relay_bp.RelayDecoderF32(d,error_priors=a['p'].astype(np.float64),gamma0=.1,pre_iter=80,num_sets=100,set_max_iter=60,gamma_dist_interval=(-.24,.66),stop_nconv=5)
        fn=lambda s:backend.decode(s)
    else:
        backend=decoders.make_solver(d,a['p'],engine);fn=lambda s:backend.decode(s).copy()
    startup=time.perf_counter()-start
    fn(ss[0]);[h.stats.clear() for h in objects]
    latency=[];fail=[];pred=[];corrections=[];invalid=[]
    journal=(RESULTS/(model+'__'+engine+'__shots.jsonl')).open('w')
    for i,s in enumerate(ss):
        t=time.perf_counter_ns();x=fn(s);latency.append(time.perf_counter_ns()-t)
        if engine=='Tesseract':y=np.asarray(x,dtype=np.uint8);bad=False
        else:
            x=np.asarray(x,dtype=np.uint8);bad=not np.array_equal(d@x%2,s);y=np.asarray(l@x%2,dtype=np.uint8)
            corrections.append(np.packbits(x,bitorder='little'))
        invalid.append(bad);pred.append(y);fail.append(bool(bad or np.any(y!=obs[i])))
        journal.write(json.dumps(dict(shot=i,latency_ns=latency[-1],failure=fail[-1],invalid=bad,prediction=y.tolist(),correction_sha256=hashlib.sha256(np.asarray(x).tobytes()).hexdigest() if engine!='Tesseract' else None))+'\n');journal.flush()
    journal.close()
    traces=[t for h in objects for t in h.stats]
    # Separate, instrumented memory pass. Native allocations are included
    # in process RSS; durations above have no RSS polling overhead.
    baseline=rss();peak=[baseline];stop=threading.Event()
    def monitor():
        while not stop.wait(.001):peak[0]=max(peak[0],rss())
    thread=threading.Thread(target=monitor);thread.start()
    for s in ss[:min(4,len(ss))]:fn(s)
    stop.set();thread.join();peak[0]=max(peak[0],rss())
    durations=np.array(latency)/1e6
    result=dict(model=model,engine=engine,shots=len(ss),failures=sum(fail),invalid=None if engine=='Tesseract' else sum(invalid),
        startup_s=startup,mean_ms=float(durations.mean()),p50_ms=float(np.quantile(durations,.5)),p95_ms=float(np.quantile(durations,.95)),p99_ms=float(np.quantile(durations,.99)),
        memory_pass_peak_rss_bytes=peak[0],pre_memory_pass_rss_bytes=baseline,os_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        detectors=d.shape[0],faults=d.shape[1],max_row_degree=int(d.getnnz(axis=1).max()),max_col_degree=int(d.getnnz(axis=0).max()),
        model_hash=sha(path/'D.npz'),samples_hash=sha(path/'samples.npz'),peak_cluster=max((t['peak_cluster'] for t in traces),default=None),
        cluster_peak_quantiles=np.quantile([t['peak_cluster'] for t in traces],[.5,.95,.99]).tolist() if traces else None,
        timing_scope='full Seamwise repair1 for HUF/SW/BPHUF/BPSW; full joint decode for external baselines',
        backend_scope=('BP-assisted residual HUF reference' if engine.startswith('BP') else 'new Python HUF reference with shared terminal canonicalization; no BP') if objects else 'native external backend',process_budget_seconds=budget)
    stem=RESULTS/(model+'__'+engine)
    np.savez_compressed(str(stem)+'.npz',latency_ns=latency,failures=fail,invalid=invalid,predictions=pred,corrections=corrections)
    Path(str(stem)+'.json').write_text(json.dumps(result,indent=2))
    Path(str(stem)+'__clusters.json').write_text(json.dumps(traces))
    print(json.dumps(result),flush=True)

def suite():
    results=[]
    models=sorted(p.name for p in DATA.iterdir() if (p/'D.npz').exists())
    # Fixed count independent of failures. Original primary case has 256
    # identical stored shots; other configurations use a 64-shot pilot.
    for model in models:
        count=256 if model=='surface_d5_p0.006_B4' else 64
        for engine in ['HUF','SW','Tesseract','LSD2','OSD2']:
            out=RESULTS/(model+'__'+engine+'.json')
            if out.exists() and json.loads(out.read_text())['shots']==count:continue
            with (RESULTS/(model+'__'+engine+'.log')).open('w') as log:
                try:
                    job=subprocess.run([sys.executable,__file__,'--child',model,engine,str(count)],stdout=log,stderr=subprocess.STDOUT,timeout=180)
                    if job.returncode:results.append(dict(model=model,engine=engine,status='ERROR',exitcode=job.returncode))
                except subprocess.TimeoutExpired:results.append(dict(model=model,engine=engine,status='TIMEOUT',budget_s=180))
            print(model,engine,'complete' if out.exists() else 'unavailable',flush=True)
    (RESULTS/'execution_failures.json').write_text(json.dumps(results,indent=2))

if __name__=='__main__':
    if sys.argv[1]=='--child':child(sys.argv[2],sys.argv[3],int(sys.argv[4]))
    else:suite()
