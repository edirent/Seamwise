"""Preservation check and self-contained evidence archive after measurements."""
import sys,pathlib,json,time,hashlib,tarfile,os
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from freeze_guard import verify_lock
lock=verify_lock();index=json.loads((ROOT/'results/P4_run_index.json').read_text());assert index['status'] in ['COMPLETE','ERROR']
checked_data=0
samples=json.loads((ROOT/'results/new_samples/manifest.json').read_text())
for item in samples['workloads'].values():
 for split in item['splits'].values():
  assert sha(ROOT/split['path'])==split['sha256'],'Frozen sample content changed'
  checked_data+=1
pools=json.loads((ROOT/'results/prepared_pools/manifest.json').read_text())
for name,h in pools['files'].items():
 assert sha(ROOT/name)==h,'Frozen pool content changed'
 checked_data+=1
for name in ['ACCURACY_RESULTS.md','LATENCY_RESULTS.md','POLICY_ABLATION.md','SOLVER_COMPARISON.md','PARETO_FRONTIER.png','RESEARCH_DECISION_ZH.md','EXECUTION_LEDGER.json']:
 assert (ROOT/'results'/name).is_file(),name
inventory=json.loads((ROOT/'evidence/previous_framework_sha256.json').read_text());changed=[];missing=[]
for name,h in inventory.items():
 p=ROOT.parent/name
 if not p.exists():missing.append(name)
 elif sha(p)!=h:changed.append(name)
base=OLD/'artifacts/seamwise_native_research_20261109.tar.gz';expected='b1f668676e8ae8fda59c8d98596e6c931d05745fe1638d6d3af2c7686d99e3a1';assert sha(base)==expected
preserve=dict(status='PASS' if not changed and not missing else 'FAIL',verified_files=len(inventory),changed=changed,missing=missing,base_archive_sha256=expected,verified_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()));atomic(ROOT/'evidence/previous_framework_preservation.json',preserve);assert preserve['status']=='PASS',preserve
# Verify that every recorded confirmatory access follows the original lock time.
access=[]
for f in sorted((ROOT/'results').glob('P4*/*/*/truth_access.json')):
 x=json.loads(f.read_text());assert x['lock_sha256']==sha(ROOT/'configs/confirmatory_lock.json') and x['utc']>=lock['created_utc'];access.append(dict(path=str(f.relative_to(ROOT)),**x))
atomic(ROOT/'evidence/confirmatory_access_audit.json',dict(status='PASS',lock_created_utc=lock['created_utc'],accesses=access,source_and_binary_lock_verified=True))
# Include source, all raw data/results/logs, and the measured modules, but no object caches.
paths=[]
for p in ROOT.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(ROOT)
 if '__pycache__' in rel.parts or '.pytest_cache' in rel.parts or rel.parts[0]=='artifacts':continue
 if rel.parts[0].startswith('build'):
  if not (p.name.startswith('_accuracy_native') and p.suffix=='.so' or p.name in ['compile_commands.json','CMakeCache.txt','accuracy_tests']):continue
 if str(rel) in ['evidence/final_file_sha256.json','evidence/RESULT_SEAL.json','evidence/seal_results.log','evidence/archive_verification.json']:continue
 paths.append(p)
files={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)};atomic(ROOT/'evidence/final_file_sha256.json',files)
seal=dict(status='SEALED',created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),files=len(files),frozen_data_and_pool_files_verified=checked_data,file_inventory_sha256=sha(ROOT/'evidence/final_file_sha256.json'),policy_lock_sha256=sha(ROOT/'configs/confirmatory_lock.json'),original_preservation=preserve,base_dependency=dict(member='base_dependency/'+base.name,sha256=expected),P4_status=index['status'],P4_elapsed_s=index.get('elapsed_s'),scope='New accuracy research with preserved prior evidence; no change to original manuscript/results; archive digest is external to avoid a self-referential hash')
atomic(ROOT/'evidence/RESULT_SEAL.json',seal);paths += [ROOT/'evidence/final_file_sha256.json',ROOT/'evidence/RESULT_SEAL.json']
art=ROOT/'artifacts/seamwise_accuracy_research_20261122.tar.gz';art.parent.mkdir(exist_ok=True)
if art.exists():raise RuntimeError('Refusing to overwrite a sealed archive')
tmp=art.with_suffix(art.suffix+'.partial')
with tarfile.open(tmp,'w:gz',compresslevel=6) as tf:
 for p in sorted(paths):tf.add(p,arcname='seamwise_accuracy/'+str(p.relative_to(ROOT)),recursive=False)
 tf.add(base,arcname='base_dependency/'+base.name,recursive=False)
os.replace(tmp,art);digest=sha(art);art.with_name(art.name+'.sha256').write_text(digest+'  '+art.name+'\n')
# Read back every archived file and compare content digests, not just gzip structure.
checks=dict(files_checked=0)
with tarfile.open(art,'r:gz') as tf:
 for m in tf:
  if not m.isfile():continue
  f=tf.extractfile(m);h=hashlib.sha256()
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
  rel=m.name.removeprefix('seamwise_accuracy/');want=files.get(rel)
  if m.name=='base_dependency/'+base.name:want=expected
  elif rel in ['evidence/final_file_sha256.json','evidence/RESULT_SEAL.json']:want=sha(ROOT/rel)
  assert want is not None and h.hexdigest()==want,m.name
  checks['files_checked']+=1
atomic(ROOT/'evidence/archive_verification.json',dict(status='PASS',archive=str(art.relative_to(ROOT)),sha256=digest,bytes=art.stat().st_size,**checks))
print(json.dumps(dict(preservation=preserve,archive=str(art),sha256=digest,**checks),indent=2))
