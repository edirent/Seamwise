"""Verify the immutable P4 contract before loading evaluation samples."""
import json
from common import ROOT,OLD,sha

def verify_lock():
 lock=json.loads((ROOT/'configs/confirmatory_lock.json').read_text())
 for name,h in lock['sources'].items():
  if sha(ROOT/name)!=h:raise RuntimeError('Frozen source changed: '+name)
 for path,key in [(ROOT/'results/new_samples/manifest.json','new_dataset_manifest_sha256'),(ROOT/'results/prepared_pools/manifest.json','pool_manifest_sha256'),(next((ROOT/'build_prod').glob('_accuracy_native*.so')),'native_module_sha256'),(next((OLD/'build').glob('_native*.so')),'old_native_module_sha256')]:
  if sha(path)!=lock[key]:raise RuntimeError('Frozen artifact changed: '+str(path))
 return lock

def verify_job(job):
 lock=verify_lock();work=job['workload'];cfg=job['config']
 if job['split']=='confirmatory':
  allowed=[]
  for phase in ['primary','secondary']:
   if cfg in lock[phase+'_configs'][work]:allowed.append(lock[phase+'_count'])
 elif job['mode']=='memory':
  allowed=[lock['memory_count']] if cfg in lock['memory_configs'][work] else []
 elif job['mode']=='timing':
  allowed=[lock['timing_count']] if cfg in lock['timing_configs'][work] else []
 else:raise RuntimeError('Unknown frozen job phase')
 if job['count'] not in allowed:raise RuntimeError('Unfrozen configuration or sample count')
 return lock
