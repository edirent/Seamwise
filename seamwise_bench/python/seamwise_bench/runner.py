"""Fresh, sequential workers with stage budgets and durable decode commits."""
import json
import os
import pathlib
import resource
import signal
import subprocess
import sys
import time
import traceback
import hashlib
import numpy as np
from .common import ROOT,atomic,digest,sha,unique_run,pin,UnsupportedModel
from .datasets import verify_manifest,frozen_model
from .adapters import make
from .audit import environment
from .fidelity import source_hashes

SCOPE="prepared_online_detector_bits_to_observable_frame_batch1"
class StageTimeout(TimeoutError):pass
def alarm_handler(signum,frame):raise StageTimeout("stage wall-clock budget exceeded")
def rss():
    import psutil
    return psutil.Process().memory_info().rss

def check_gate():
    p=ROOT/"evidence"/"fidelity_gate.json"
    v=json.loads(p.read_text())
    if v["status"]!="PASS":raise RuntimeError("fidelity gate has not passed")
    current=source_hashes()
    # Infrastructure changes cannot change decoding; C++ changes must rerun.
    before={k:h for k,h in v["source_hashes"].items() if k.startswith("cpp/")}
    after={k:h for k,h in current.items() if k.startswith("cpp/")}
    if before!=after:raise RuntimeError("stale C++ fidelity gate")

def worker(jobpath):
    cpu=pin();signal.signal(signal.SIGALRM,alarm_handler)
    job=json.loads(pathlib.Path(jobpath).read_text());out=pathlib.Path(job["directory"])
    cfg=job["backend"];manifest=verify_manifest(job["manifest"]);item=manifest["workloads"][job["workload"]]
    env=environment()
    timing_scope="instrumented_memory_decode_not_publication_latency" if job["mode"]=="memory" else "audit_instrumented_decode_not_publication_latency" if job["mode"]=="diagnostics" else SCOPE
    summary=dict(job_id=job["job_id"],workload=job["workload"],backend=cfg["name"],backend_config=cfg,config_hash=digest(cfg),
                 model_hash=item["model_hash"],sample_hash=item["splits"][job["split"]]["sha256"],
                 mode=job["mode"],split=job["split"],repetition=job["repetition"],scope=timing_scope,threads=1,cpu=cpu,batch=1,
                 requested=job["count"],completed=0,status="ERROR",stage="load",budgets=job["budgets"],versions=env["versions"],binary_sha256=env["binary_sha256"],backend_binary_fingerprint=digest(env["binary_sha256"]),source_hash=digest(source_hashes()))
    summary["background_loadavg_start"]=env["loadavg"]
    try:
        signal.alarm(job["budgets"]["preparation"]);t=time.perf_counter_ns()
        atomic(out/"stage.json",dict(stage="preparation",started_monotonic=time.monotonic(),budget_s=job["budgets"]["preparation"]))
        model=frozen_model(item);raw=np.load(ROOT/item["splits"][job["split"]]["path"])
        detectors=raw["detectors"];observables=raw["observables"]
        warm=np.load(ROOT/item["splits"]["validation"]["path"])["detectors"][:job.get("warmup",16)]
        # Record baseline after libraries load and before decoder construction.
        import importlib
        if cfg.get("build"):sys.path.insert(0,str(ROOT/cfg["build"]))
        modules={"native":["_native"],"python":["huf","bp_huf","decoders"],"lsd":["ldpc"],"osd":["ldpc"],"relay":["relay_bp"],"tesseract":["tesseract_decoder"],"gari":["_gari"]}[cfg["kind"]]
        for module in modules:importlib.import_module(module)
        summary["load_and_import_ns"]=time.perf_counter_ns()-t
        baseline=rss();summary["rss_after_library_load_bytes"]=baseline
        preparation_started=time.perf_counter_ns()
        backend=make(model,cfg,audit=job["mode"]=="diagnostics")
        summary["preparation_ns"]=time.perf_counter_ns()-preparation_started;summary["load_prepare_ns"]=time.perf_counter_ns()-t;summary["rss_after_prepare_bytes"]=rss()
        summary["resolved_backend_config"]=getattr(backend,"resolved_config",cfg)
        if cfg["kind"] in ["native","gari"]:
            module=sys.modules["_native" if cfg["kind"]=="native" else "_gari"]
            summary["native_binary_sha256"]=sha(module.__file__)
        summary["stage"]="decode"
        decode_started=time.monotonic()
        atomic(out/"stage.json",dict(stage="decode",substage="warmup",started_monotonic=decode_started,budget_s=job["budgets"]["decode"]))
        signal.alarm(job["budgets"]["decode"])
        warmup_started=time.perf_counter_ns()
        for s in warm:backend.decode(s)
        summary["warmup_ns"]=time.perf_counter_ns()-warmup_started;summary["warmup_shots"]=len(warm)
        atomic(out/"stage.json",dict(stage="decode",substage="online",started_monotonic=decode_started,budget_s=job["budgets"]["decode"]))
        if hasattr(backend,"backend") and hasattr(backend.backend,"clear_diagnostics"):backend.backend.clear_diagnostics()
        permutation=np.random.default_rng(job["permutation_seed"]).permutation(job["count"])
        rows=[];start=time.perf_counter_ns()
        with (out/"shots.jsonl.partial").open("x") as journal:
            for idx in permutation:
                s=detectors[idx]
                t=time.perf_counter_ns();frame,x=backend.decode(s);elapsed=time.perf_counter_ns()-t
                frame=np.asarray(frame,dtype=np.uint8)
                if frame.shape!=(model["l"].shape[0],) or np.any(frame>1):raise ValueError("observable output contract")
                valid=None if x is None else bool(np.array_equal(model["d"]@x%2,s))
                logical_failure=bool(np.any(frame!=observables[idx]))
                failure=bool(logical_failure or valid is False)
                r=dict(sample_id=item["splits"][job["split"]]["sample_id_prefix"]+":"+str(idx),shot=int(idx),status="COMPLETE",latency_ns=elapsed,
                       failure=failure,logical_failure=logical_failure,service_failure=valid is False,marginal_observable_failures=(frame!=observables[idx]).astype(int).tolist(),valid=valid,
                       prediction=frame.tolist(),observable_sha256=hashlib.sha256(np.packbits(frame,bitorder="little").tobytes()).hexdigest(),
                       correction_sha256=None if x is None else hashlib.sha256(np.asarray(x,dtype=np.uint8).tobytes()).hexdigest(),
                       backend_config_hash=summary["config_hash"],scope=timing_scope,threads=1,cpu=cpu,model_hash=item["model_hash"])
                retained=r if job["mode"]!="memory" else {k:r[k] for k in ["latency_ns","failure","valid"]}
                rows.append(retained);journal.write(json.dumps(r,separators=(",",":"))+"\n");journal.flush();summary["completed"]=len(rows)
                if valid is False:
                    declared_nonconvergence=False
                    if cfg["kind"]=="relay":
                        detailed=backend.backend.decode_detailed(s)
                        declared_nonconvergence=not detailed.success
                        if not np.array_equal(detailed.decoding,x):raise ValueError("Relay detailed/public output mismatch")
                    if (cfg["kind"]=="gari" or declared_nonconvergence) and job["mode"]=="validation":
                        # Bounded diagnostic validation may quantify NMS
                        # nonconvergence; it cannot enter publication timing.
                        if not (out/"nonconvergence_reproducer.json").exists():atomic(out/"nonconvergence_reproducer.json",dict(shot=int(idx),syndrome=s.tolist(),correction=np.asarray(x).tolist(),config=cfg))
                    else:
                        atomic(out/"invalid_reproducer.json",dict(shot=int(idx),syndrome=s.tolist(),correction=np.asarray(x).tolist(),config=cfg))
                        raise ValueError("invalid correction; publication runs stopped")
        summary["decode_pass_wall_ns"]=time.perf_counter_ns()-start
        summary["prepared_decode_sum_ns"]=sum(r["latency_ns"] for r in rows)
        summary["lifecycle_decoder_work_ns"]=summary["load_prepare_ns"]+summary["warmup_ns"]+summary["prepared_decode_sum_ns"]
        summary["lifecycle_decoder_calls"]=len(rows)+len(warm)
        os.replace(out/"shots.jsonl.partial",out/"shots.jsonl")
        times=np.array([r["latency_ns"] for r in rows]);summary.update(status="COMPLETE",stage="decode_committed",failures=sum(r["failure"] for r in rows),invalid=sum(r["valid"] is False for r in rows),
                         validity="UNAVAILABLE" if all(r["valid"] is None for r in rows) else "INVALID_CORRECTIONS" if any(r["valid"] is False for r in rows) else "PASS",
                         latency_ns=dict(mean=float(times.mean()),median=float(np.median(times)),p95=float(np.quantile(times,.95)),p99=float(np.quantile(times,.99)),maximum=int(times.max())))
        signal.alarm(0);atomic(out/"decode_summary.json",summary)
        if job["mode"]=="diagnostics" and hasattr(backend.backend,"diagnostics"):atomic(out/"diagnostics.json",backend.backend.diagnostics())
        if job["mode"]=="memory":
            # Fresh worker, full corpus, histories disabled. Decode is already
            # durable before this independent instrumented soak can fail.
            summary["stage"]="memory";signal.alarm(job["budgets"]["memory"])
            atomic(out/"stage.json",dict(stage="memory",started_monotonic=time.monotonic(),budget_s=job["budgets"]["memory"]))
            del rows,times
            import gc
            gc.collect()
            audit=dict(corpus_shots=len(permutation),rss_before_full_corpus_bytes=rss(),rss_checkpoints=[],soak=[])
            import ctypes
            lib=ctypes.CDLL(None)
            allocation_pass=[]
            has_alloc=hasattr(lib,"seamwise_alloc_begin")
            if has_alloc:
                for name in ["seamwise_alloc_calls","seamwise_alloc_bytes","seamwise_alloc_frees"]:getattr(lib,name).restype=ctypes.c_uint64
            for k,idx in enumerate(permutation):
                if has_alloc:lib.seamwise_alloc_begin()
                backend.decode(detectors[idx])
                if has_alloc:
                    lib.seamwise_alloc_end();allocation_pass.append(dict(shot=int(idx),calls=lib.seamwise_alloc_calls(),requested_bytes=lib.seamwise_alloc_bytes(),frees=lib.seamwise_alloc_frees()))
                if k%max(1,len(permutation)//16)==0:audit["rss_checkpoints"].append([k,rss()])
            for round_ in range(3):
                for idx in permutation:backend.decode(detectors[idx])
                for k in range(len(permutation)):backend.decode(detectors[permutation[0]])
                audit["soak"].append(dict(round=round_,rss_bytes=rss()))
            audit["high_water_process_rss_bytes"]=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
            if hasattr(backend.backend,"diagnostics"):
                audit["native_capacity"]=backend.backend.diagnostics()
            audit["allocation_counts"]=allocation_pass if has_alloc else "UNAVAILABLE"
            audit["allocation_scope"]="diagnostic glibc malloc/calloc/realloc requests on calling thread for complete adapter; includes conversion; requested bytes are not live bytes; not an RSS subtraction"
            atomic(out/"memory.json",audit);summary["stage"]="memory_committed"
        signal.alarm(0)
    except BaseException as e:
        signal.alarm(0)
        summary["error"]=repr(e);summary["traceback"]=traceback.format_exc()
        if isinstance(e,StageTimeout):summary["status"]="MEMORY_AUDIT_FAILED" if summary["stage"]=="memory" else "PREPARATION_TIMEOUT" if summary["stage"]=="load" else "DECODE_TIMEOUT"
        else:summary["status"]="UNSUPPORTED" if isinstance(e,UnsupportedModel) else "ERROR"
    summary["missing"]=summary["requested"]-summary["completed"]
    summary["high_water_process_rss_bytes"]=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    usage=resource.getrusage(resource.RUSAGE_SELF);summary["process_user_cpu_s"]=usage.ru_utime;summary["process_system_cpu_s"]=usage.ru_stime
    summary["background_loadavg_end"]=os.getloadavg()
    atomic(out/"summary.json",summary)
    return summary

def launch_worker(job,log,env,command=None):
    """Parent watchdog also interrupts native calls that defer Python signals."""
    out=pathlib.Path(job["directory"]);started=time.monotonic()
    command=command or [sys.executable,"-m","seamwise_bench.runner","--worker",str(out/"job.json")]
    process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env)
    while process.poll() is None:
        phase=dict(stage="preparation",started_monotonic=started,budget_s=job["budgets"]["preparation"])
        if (out/"stage.json").exists():
            try:phase=json.loads((out/"stage.json").read_text())
            except (OSError,json.JSONDecodeError):pass
        if time.monotonic()-phase["started_monotonic"]>phase["budget_s"] or time.monotonic()>job.get("campaign_deadline_monotonic",float('inf')):
            process.kill();process.wait()
            summary=json.loads((out/"decode_summary.json").read_text()) if (out/"decode_summary.json").exists() else dict(job_id=job["job_id"],workload=job["workload"],backend=job["backend"]["name"],backend_config=job["backend"],requested=job["count"],completed=0)
            journal=out/"shots.jsonl.partial"
            if journal.exists():summary["completed"]=sum(1 for _ in journal.open())
            summary.update(status="MEMORY_AUDIT_FAILED" if phase["stage"]=="memory" else "PREPARATION_TIMEOUT" if phase["stage"]=="preparation" else "DECODE_TIMEOUT",stage="parent_watchdog_"+phase["stage"],substage=phase.get("substage"),watchdog_budget_s=phase["budget_s"],missing=job["count"]-summary["completed"])
            atomic(out/"summary.json",summary);return summary
        try:process.wait(timeout=.2)
        except subprocess.TimeoutExpired:pass
    if (out/"summary.json").exists():return json.loads((out/"summary.json").read_text())
    return dict(job_id=job["job_id"],workload=job["workload"],backend=job["backend"]["name"],backend_config=job["backend"],status="ERROR",exitcode=process.returncode,requested=job["count"],completed=0,missing=job["count"],stage="worker_crash")

def run(manifestpath,config,mode="timing",split=None):
    check_gate();manifestpath=pathlib.Path(manifestpath).resolve();manifest=verify_manifest(manifestpath)
    if "frozen_campaign" in manifest:
        frozen=manifest["frozen_campaign"]
        if digest(config)!=digest(frozen["config"]):raise ValueError("configuration differs from frozen campaign")
        if source_hashes()!=frozen["sources"]:raise ValueError("source differs from frozen campaign")
    out=unique_run(mode);atomic(out/"environment.json",environment());atomic(out/"config.json",config)
    atomic(out/"sources.json",source_hashes());ledger=[]
    split=split or ("timing" if mode in ["timing","memory"] else "test" if mode=="accuracy" else "validation")
    if split=="test" and "frozen_campaign" not in manifest:raise ValueError("test observations require a frozen campaign")
    repeats=config.get("repetitions",1) if mode=="timing" else 1
    rng=np.random.default_rng(config.get("order_seed",202611091))
    schedule=[]
    for name in config.get("workloads",manifest["workloads"].keys()):
        for rep in range(repeats):
            order=rng.permutation(len(config["backends"])).tolist()
            schedule.append(dict(workload=name,repetition=rep,backend_order=[config["backends"][i]["name"] for i in order],permutation_seed=202611090+rep))
    atomic(out/"schedule.json",schedule)
    campaign_started=time.monotonic()
    for block in schedule:
        for bn in block["backend_order"]:
            cfg=next(c for c in config["backends"] if c["name"]==bn)
            cfg=config.get("workload_backend_overrides",{}).get(block["workload"],{}).get(bn,cfg)
            job_id=f"{block['workload']}__{bn}__r{block['repetition']}";dest=out/job_id;dest.mkdir()
            count=min(config.get("count",manifest["workloads"][block["workload"]]["splits"][split]["shots"]),manifest["workloads"][block["workload"]]["splits"][split]["shots"])
            job=dict(job_id=job_id,manifest=str(manifestpath),directory=str(dest),backend=cfg,workload=block["workload"],mode=mode,split=split,count=count,
                     repetition=block["repetition"],permutation_seed=block["permutation_seed"],warmup=config.get("warmup",16),
                     budgets=config.get("budgets",dict(preparation=120,decode=300,memory=120)))
            cap=config.get("stage_wall_budgets",{}).get(mode,config.get("campaign_wall_budget_s",1e99))
            job["campaign_deadline_monotonic"]=campaign_started+cap
            atomic(dest/"job.json",job)
            deferred=config.get("deferred_jobs",{}).get(block["workload"],{}).get(bn)
            if isinstance(deferred,dict):deferred=deferred.get(mode)
            if deferred:
                summary=dict(job_id=job_id,workload=block["workload"],backend=bn,backend_config=cfg,status="UNSUPPORTED",stage="predeclared_budget_deferred",reason=deferred,backend_available=True,completed=0,requested=count,missing=count)
                atomic(dest/"summary.json",summary);ledger.append(summary);atomic(out/"execution_ledger.json",ledger);continue
            stage_cap=config.get("stage_wall_budgets",{}).get(mode,config.get("campaign_wall_budget_s",1e99))
            if time.monotonic()-campaign_started>stage_cap:
                summary=dict(job_id=job_id,workload=block["workload"],backend=bn,backend_config=cfg,status="DECODE_TIMEOUT",stage="not_started_campaign_budget",completed=0,requested=count,missing=count)
                atomic(dest/"summary.json",summary);ledger.append(summary);atomic(out/"execution_ledger.json",ledger);continue
            started=time.monotonic()
            with (dest/"worker.log").open("x") as log:
                env=os.environ.copy()
                if mode=="memory" and (ROOT/"build"/"liballoc_audit.so").exists():env["LD_PRELOAD"]=str(ROOT/"build"/"liballoc_audit.so")
                summary=launch_worker(job,log,env)
            summary["worker_wall_seconds"]=time.monotonic()-started
            ledger.append(summary);atomic(out/"execution_ledger.json",ledger)
            print(f"{out.name} {job_id} {summary['status']} {summary.get('completed',0)}/{count}",flush=True)
            if summary["status"]=="ERROR" and (dest/"invalid_reproducer.json").exists():raise RuntimeError("correctness gate failed; stopped campaign")
    atomic(out/"run.json",dict(status="COMPLETE" if all(j["status"]=="COMPLETE" for j in ledger) else "PARTIAL",mode=mode,split=split,manifest=str(manifestpath.relative_to(ROOT)),manifest_sha256=sha(manifestpath),config=config))
    return out

if __name__=="__main__":
    if len(sys.argv)==3 and sys.argv[1]=="--worker":worker(sys.argv[2])
    else:raise SystemExit("internal worker entry point")
