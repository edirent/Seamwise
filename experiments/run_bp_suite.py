"""Run ONLY after run.py --suite ends: no overlapping timing workloads."""
import subprocess,sys,json
from pathlib import Path
here=Path(__file__).resolve().parent
statuses=[]
for model in sorted(p.name for p in (here/'data').iterdir() if (p/'D.npz').exists()):
 count=256 if model=='surface_d5_p0.006_B4' else 64
 for engine in ['BPHUF','BPSW']:
  out=here/'results'/(model+'__'+engine+'.json')
  if out.exists():continue
  with (here/'results'/(model+'__'+engine+'.log')).open('w') as log:
   try:r=subprocess.run([sys.executable,str(here/'run.py'),'--child',model,engine,str(count)],stdout=log,stderr=subprocess.STDOUT,timeout=210)
   except subprocess.TimeoutExpired:r=None
  statuses.append(dict(model=model,engine=engine,status='COMPLETE' if out.exists() else ('PROCESS_TIME_BUDGET_EXCEEDED' if r is None or r.returncode==-14 else 'ERROR'),returncode=r.returncode if r is not None else None))
  (here/'results'/'execution_failures_bp.json').write_text(json.dumps(statuses,indent=2))
  print(model,engine,'complete' if out.exists() else 'budget-limited/error',flush=True)
