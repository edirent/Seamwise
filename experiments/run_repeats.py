"""Separate primary timing replication; reused samples do not increase N."""
import os,sys,json,subprocess
from pathlib import Path
import numpy as np
here=Path(__file__).resolve().parent;rng=np.random.default_rng(774411)
models=['surface_d5_p0.006_B4','bb144_p0.015_B4'];methods=['BPHUF','BPSW','Tesseract']
for model in models:
 for rep in range(3):
  target=here/'timing_replicates'/f'{model}_r{rep}';target.mkdir(parents=True,exist_ok=True)
  for engine in rng.permutation(methods):
   out=target/(model+'__'+engine+'.json')
   if out.exists():continue
   env=os.environ.copy();env['SEAMWISE_RESULTS_DIR']=str(target)
   with (target/(engine+'.log')).open('w') as log:
    try:subprocess.run([sys.executable,str(here/'run.py'),'--child',model,engine,'64'],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=210)
    except subprocess.TimeoutExpired:pass
   print('replicate',rep,engine,'complete' if out.exists() else 'incomplete',flush=True)
rows=[]
for p in (here/'timing_replicates').glob('*_r*/*.json'):
 if '__clusters' not in p.name:
  r=json.loads(p.read_text());r['replicate']=p.parent.name;rows.append(r)
(here/'timing_replicates'/'summary.json').write_text(json.dumps(rows,indent=2))
checks=[]
for row in rows:
 folder=here/'timing_replicates'/row['replicate']
 stem=row['model']+'__'+row['engine']+'.npz'
 a=np.load(folder/stem);b=np.load(here/'results'/stem)
 mismatch=int(np.any(a['predictions']!=b['predictions'][:64],axis=1).sum())
 assert mismatch==0
 checks.append(dict(model=row['model'],engine=row['engine'],replicate=row['replicate'],prediction_mismatches=mismatch))
(here/'timing_replicates'/'fidelity_reuse_audit.json').write_text(json.dumps(checks,indent=2))
