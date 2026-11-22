import pathlib,json,itertools,collections
import numpy as np
from common import *

def read_run(path):
 path=pathlib.Path(path);points=[];incomplete=[];samples={};binaries={};repeated={};runtime=None
 for job in json.loads((path/'EXECUTION_LEDGER.json').read_text()):
  if job['status']!='COMPLETE':incomplete.append(job);continue
  assert job['scope']=='prepared_online_detector_bits_to_observable_frame_batch1' and job['threads']==1 and job['batch']==1
  assert job.get('versions') and job.get('binary_sha256')
  assert all(v and str(v).lower() not in ['unknown','unavailable','none'] for v in job['versions'].values())
  provenance=(job['versions'],job['binary_sha256'],job.get('provenance_commits'),job['cpu'],job['threads'],job['batch'])
  if runtime is None:runtime=provenance
  else:assert provenance==runtime,'Dependency or resource drift within run'
  if job['config'].get('kind','new') in ['new','original']:assert job.get('native_module_sha256')
  work=job['workload'];sample=job['sample_sha256'];assert samples.get(work,sample)==sample;samples[work]=sample
  rows=sorted([json.loads(s) for s in (pathlib.Path(job['directory'])/'shots.jsonl').read_text().splitlines()],key=lambda x:x['sample_id']);assert len(rows)==job['count'] and len({r['sample_id'] for r in rows})==len(rows)
  key=(work,job['config']['name']);signature=(job['config_sha256'],job.get('native_module_sha256'),[(r['sample_id'],r['prediction'],r['correction_sha256'],r['invalid']) for r in rows])
  if key in repeated:assert signature==repeated[key],'Nondeterministic repeated outputs or configuration drift'
  repeated[key]=signature
  n=len(rows);k=sum(r['logical_failure'] for r in rows);inv=sum(r['invalid'] for r in rows);times=np.array([r['latency_ns'] for r in rows])/1e6
  points.append(dict(workload=work,name=job['config']['name'],config=job['config'],run=str(path.relative_to(ROOT)),repetition=job['repetition'],n=n,failures=k,invalid=inv,failure_rate=k/n,wilson95=wilson(k,n),mean_ms=float(times.mean()),median_ms=float(np.median(times)),p95_ms=float(np.quantile(times,.95)),p99_ms=float(np.quantile(times,.99)),max_ms=float(times.max()),baseline_rss_bytes=job['baseline_rss_bytes'],prepared_rss_bytes=job['prepared_rss_bytes'],high_water_rss_bytes=job['high_water_rss_bytes'],preparation_ms=job['preparation_ns']/1e6,source_module_sha256=job.get('native_module_sha256'),rows=rows))
 return points,incomplete

def save_analysis(path):
 points,incomplete=read_run(path);comparisons=[];by=collections.defaultdict(list)
 for p in points:by[p['workload']].append(p)
 planned=json.loads((pathlib.Path(path)/'planned_configs.json').read_text())
 comparisons_planned=sum(len(ps)*(len(ps)-1)//2 for ps in planned.values())
 alpha=.05/max(1,comparisons_planned)
 for work,ps in by.items():
  for a,b in itertools.combinations(ps,2):
   assert [r['sample_id'] for r in a['rows']]==[r['sample_id'] for r in b['rows']]
   comparisons.append(dict(workload=work,A=a['name'],B=b['name'],paired=paired([r['logical_failure'] for r in a['rows']],[r['logical_failure'] for r in b['rows']],alpha)))
 result=dict(summary=[{k:v for k,v in p.items() if k!='rows'} for p in points],incomplete=incomplete,comparisons=comparisons,scope='validation exploratory unless a separately frozen confirmatory run; raw prefixes never used as completed rates')
 atomic(pathlib.Path(path)/'analysis.json',result);return result
