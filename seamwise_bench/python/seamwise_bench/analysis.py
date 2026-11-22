"""Paired accuracy inference and hierarchically paired timing estimates."""
import collections
import itertools
import json
import math
import pathlib
import numpy as np
from scipy.stats import beta,norm
from .common import ROOT,atomic,digest
from .runner import SCOPE

def wilson(k,n,alpha=.05):
    if not n:return [None,None]
    z=norm.ppf(1-alpha/2);p=k/n;den=1+z*z/n
    c=(p+z*z/(2*n))/den;r=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0.,c-r),min(1.,c+r)]

def cp_lower(k,n,a):return 0. if k==0 else float(beta.ppf(a,k,n-k+1))
def cp_upper(k,n,a):return 1. if k==n else float(beta.ppf(1-a,k+1,n-k))

def paired(a,b,alpha=.05):
    a=np.asarray(a,dtype=bool);b=np.asarray(b,dtype=bool);n=len(a)
    if n!=len(b) or not n:raise ValueError("paired observations required")
    cells=dict(both_correct=int(np.sum(~a&~b)),only_A_wrong=int(np.sum(a&~b)),only_B_wrong=int(np.sum(~a&b)),both_wrong=int(np.sum(a&b)))
    aa,bb,cc=cells['only_A_wrong'],cells['only_B_wrong'],cells['both_wrong']
    # Simultaneous one-sided CP cell bounds; union bound provides coverage
    # without assuming the four multinomial cells are independent groups.
    u=cp_upper(aa,n,alpha/3)-1.1*cp_lower(bb,n,alpha/3)-.1*cp_lower(cc,n,alpha/3)
    lo=cp_lower(aa,n,alpha/4)-cp_upper(bb,n,alpha/4)
    hi=cp_upper(aa,n,alpha/4)-cp_lower(bb,n,alpha/4)
    return dict(n=n,cells=cells,risk_difference=float(np.mean(a)-np.mean(b)),risk_difference_interval=[lo,hi],
                noninferiority_relative_margin=.10,noninferiority_contrast=float(np.mean(a)-1.1*np.mean(b)),noninferiority_one_sided_upper=u,
                noninferiority="PASS" if u<=0 else "INCONCLUSIVE_OR_INELIGIBLE",strict_equality_target_one_sided_upper=cp_upper(aa,n,alpha/2)-cp_lower(bb,n,alpha/2),
                alpha=alpha,coverage="Bonferroni simultaneous exact binomial cell bounds for paired multinomial outcomes; conservative")

def timing_ratio(a,b,seed=129,draws=600):
    a=np.asarray(a);b=np.asarray(b)
    if a.shape!=b.shape or a.ndim!=2:raise ValueError("matched repetition and sample matrices required")
    rng=np.random.default_rng(seed);r,n=a.shape;boot=[]
    for _ in range(draws):
        reps=rng.integers(r,size=r);shots=rng.integers(n,size=n)
        boot.append(float(a[np.ix_(reps,shots)].mean()/b[np.ix_(reps,shots)].mean()))
    return dict(ratio=float(a.mean()/b.mean()),interval=np.quantile(boot,[.025,.975]).tolist(),repetitions=r,independent_sample_ids=n,
                uncertainty="paired hierarchical bootstrap; resample repetition blocks and shared independent sample IDs",bootstrap_draws=draws)

def read_run(path):
    path=pathlib.Path(path)
    ledger=json.loads((path/"execution_ledger.json").read_text());groups=collections.defaultdict(list);incomplete=[]
    snapshot=json.loads((path/"environment.json").read_text()) if (path/"environment.json").exists() else {}
    reference_inputs={};operating_points={}
    for job in ledger:
        if job["status"]!="COMPLETE":incomplete.append(job);continue
        if job["scope"]!=SCOPE or job["threads"]!=1 or job["batch"]!=1:raise ValueError("mixed timing scope/resources")
        required={"native":["numpy"],"python":["numpy","scipy","ldpc"],"tesseract":["numpy","stim","tesseract-decoder"],"lsd":["numpy","scipy","ldpc"],"osd":["numpy","scipy","ldpc"],"relay":["numpy","scipy","relay-bp"],"gari":["numpy","scipy"]}[job["backend_config"]["kind"]]
        if any(job["versions"].get(k) in [None,"UNAVAILABLE"] for k in required):raise ValueError("unknown backend version")
        inputs=(job["model_hash"],job["sample_hash"])
        if job["workload"] in reference_inputs and reference_inputs[job["workload"]]!=inputs:raise ValueError("mismatched model/sample hashes")
        reference_inputs[job["workload"]]=inputs
        binary=job.get("backend_binary_fingerprint") or (digest(snapshot["binary_sha256"]) if snapshot.get("binary_sha256") else None)
        if binary is None:raise ValueError("unknown actual binary fingerprint")
        point=(job["config_hash"],digest(job["versions"]),binary,job.get("native_binary_sha256"),job["cpu"])
        key=(job["workload"],job["backend"])
        if key in operating_points and operating_points[key]!=point:raise ValueError("backend/configuration/resource changed across repetitions")
        operating_points[key]=point
        rows=[json.loads(x) for x in (path/job["job_id"]/"shots.jsonl").read_text().splitlines()]
        if len(rows)!=job["requested"]:raise ValueError("silent missing shots")
        rows=sorted(rows,key=lambda r:r["sample_id"])
        if any(r["scope"]!=job["scope"] or r["backend_config_hash"]!=job["config_hash"] or r["model_hash"]!=job["model_hash"] for r in rows):raise ValueError("row contract differs from process summary")
        if len({r["sample_id"] for r in rows})!=len(rows):raise ValueError("duplicate sample IDs")
        groups[(job["workload"],job["backend"])].append((job,rows))
    return groups,incomplete

def analyze(path):
    path=pathlib.Path(path)
    if (path/"run.json").exists() and json.loads((path/"run.json").read_text())["mode"]=="memory":return analyze_memory(path)
    groups,incomplete=read_run(path);summary=[];comparisons=[];bywork=collections.defaultdict(dict)
    for (work,name),records in groups.items():
        records.sort(key=lambda z:z[0]["repetition"]);first=records[0][1];ids=[r["sample_id"] for r in first]
        for j,rows in records:
            if [r["sample_id"] for r in rows]!=ids:raise ValueError("mismatched sample sets across repetitions")
            if [(r["prediction"],r["correction_sha256"]) for r in rows]!=[(r["prediction"],r["correction_sha256"]) for r in first]:raise ValueError("undeclared stochastic output or mutable-state leakage")
        failures=[r["logical_failure"] for r in first];timings=np.array([[r["latency_ns"] for r in rr] for _,rr in records])
        n=len(first);k=sum(failures)
        row=dict(workload=work,backend=name,n_independent=n,failures=k,failure_rate=k/n,wilson95=wilson(k,n),
                 service_failures=sum(r["service_failure"] for r in first),service_inclusive_failures=sum(r["failure"] for r in first),
                 zero_failure_one_sided95_upper=cp_upper(0,n,.05) if k==0 else None,precision="INSUFFICIENT_PRECISION" if k<400 else "PLANNING_TARGET_REACHED",
                 repetitions=len(records),scope=SCOPE,mean_ms=float(timings.mean()/1e6),median_ms=float(np.median(timings)/1e6),
                 p95_ms=float(np.quantile(timings,.95)/1e6),p99_ms=float(np.quantile(timings,.99)/1e6),max_ms=float(timings.max()/1e6),
                 repetition_mean_ms=timings.mean(axis=1).tolist(),preparation_ms=[j["preparation_ns"]/1e6 for j,_ in records],
                 repetition_p99_ms=[float(np.quantile(t,.99)/1e6) for t in timings],
                 lifecycle_decoder_work_ms=[j.get("lifecycle_decoder_work_ns",j.get("load_prepare_ns",j["preparation_ns"])+int(timings[k].sum()))/1e6 for k,(j,_) in enumerate(records)],
                 lifecycle_calls=[j.get("lifecycle_decoder_calls",j["requested"]) for j,_ in records],
                 high_water_process_rss_bytes=[j["high_water_process_rss_bytes"] for j,_ in records],
                 correction_validity=records[0][0]["validity"],sample_ids=ids,config=records[0][0]["backend_config"])
        row["repetition_mean_ms"]=[x/1e6 for x in row["repetition_mean_ms"]]
        summary.append(row);bywork[work][name]=(row,failures,timings)
    # Multiplicity is fixed by the planned matrix, never reduced after observing
    # missing/failed jobs or favorable test outcomes.
    planned=json.loads((path/"config.json").read_text());k=len(planned["backends"])
    primary_pairs=len(planned.get("workloads",bywork))*k*(k-1)//2;alpha=.05/max(1,primary_pairs)
    for work,entries in bywork.items():
        for na,nb in itertools.combinations(entries,2):
            ra,a,ta=entries[na];rb,b,tb=entries[nb]
            if ra["sample_ids"]!=rb["sample_ids"]:raise ValueError("mismatched input sets across backends")
            ratio=timing_ratio(ta,tb) if ta.shape==tb.shape else None
            comparisons.append(dict(workload=work,A=na,B=nb,paired=paired(a,b,alpha),A_time_over_B_time=ratio,
                                     quality_constraint="10% relative margin; simultaneous CP bounds with familywise Bonferroni",multiplicity_comparisons=primary_pairs))
    result=dict(summary=summary,comparisons=comparisons,incomplete_jobs=incomplete,independent_accuracy_repetitions=1,
                timing_repetitions_do_not_increase_accuracy_n=True,headline_frontier="UNRESOLVED unless selected policy passes frozen independent test noninferiority gate",scope=SCOPE)
    atomic(path/"analysis.json",result)
    make_plots(path,summary,bywork)
    return result

def analyze_memory(path):
    ledger=json.loads((path/"execution_ledger.json").read_text());rows=[]
    for j in ledger:
        f=path/j["job_id"]/"memory.json"
        audit=json.loads(f.read_text()) if f.exists() else {}
        row=dict(workload=j.get("workload"),backend=j.get("backend"),status=j["status"],completed_decode_shots=j.get("completed",0),
                 baseline_after_library_load_bytes=j.get("rss_after_library_load_bytes"),after_prepare_rss_bytes=j.get("rss_after_prepare_bytes"),
                 high_water_process_rss_bytes=audit.get("high_water_process_rss_bytes",j.get("high_water_process_rss_bytes")),soak=audit.get("soak"),
                 corpus_shots=audit.get("corpus_shots"),memory_audit_available=bool(audit),scope="fresh-worker full-corpus memory and soak; no publication latency")
        if isinstance(audit.get("allocation_counts"),list):
            row['glibc_request_calls']=sum(x['calls'] for x in audit['allocation_counts']);row['glibc_requested_bytes']=sum(x['requested_bytes'] for x in audit['allocation_counts'])
        rows.append(row)
    result=dict(summary=rows,memory_only=True);atomic(path/"analysis.json",result);return result

def make_plots(path,summary,bywork):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    for work,entries in bywork.items():
        fig,ax=plt.subplots(figsize=(9,5))
        for name,(r,_,_) in entries.items():
            lo,hi=r["wilson95"];ax.errorbar(r["mean_ms"],r["failure_rate"],yerr=[[r["failure_rate"]-lo],[hi-r["failure_rate"]]],fmt='o',label=name)
        ax.set(xlabel="Prepared online mean latency (ms), one core / one thread",ylabel="Any-observable failure probability",title=work+" (exploratory unless independently frozen)");ax.legend(fontsize=6);fig.tight_layout();fig.savefig(path/(work+"_frontier.png"),dpi=160);plt.close(fig)
        fig,ax=plt.subplots(figsize=(9,5))
        for name,(r,_,times) in entries.items():
            vals=np.sort(times[0]/1e6);ax.step(vals,np.arange(1,len(vals)+1)/len(vals),where='post',label=name)
        ax.set(xlabel="Prepared online latency (ms), repetition 0",ylabel="Fraction of independent sample IDs",title=work);ax.legend(fontsize=6);fig.tight_layout();fig.savefig(path/(work+"_latency_cdf.png"),dpi=160);plt.close(fig)
