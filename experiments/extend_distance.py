"""Fixed-depth distance sweep with the recovered circuit/noise generator."""
import sys,json,subprocess
from pathlib import Path
here=Path(__file__).resolve().parent;sys.path.insert(0,str(here/'research'))
from models import save_model
statuses=[]
for d in [5,7,9,11]:
 model=f'distance_surface_d{d}_p0.003_B4_T3';path=here/'data'/model
 if not (path/'D.npz').exists():
  save_model(path,dict(id=model,family='surface',distance=d,blocks=4,rounds=3,p=.003),64,2026110940+d)
 for engine in ['HUF','SW','BPHUF','BPSW','Tesseract','LSD2','OSD2']:
  out=here/'results'/(model+'__'+engine+'.json')
  if out.exists():continue
  with (here/'results'/(model+'__'+engine+'.log')).open('w') as log:
   try:r=subprocess.run([sys.executable,str(here/'run.py'),'--child',model,engine,'64'],stdout=log,stderr=subprocess.STDOUT,timeout=70)
   except subprocess.TimeoutExpired:r=None
  statuses.append(dict(model=model,engine=engine,status='COMPLETE' if out.exists() else 'BUDGET_LIMITED_OR_ERROR',returncode=r.returncode if r else None))
  (here/'results'/'execution_failures_distance.json').write_text(json.dumps(statuses,indent=2))
  print(model,engine,'complete' if out.exists() else 'budget-limited/error',flush=True)
