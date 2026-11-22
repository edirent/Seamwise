import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from runner import run,worker
from analysis import read_run
assert not (ROOT/'configs/confirmatory_lock.json').exists()
path=ROOT/json.loads((ROOT/'results/finalists_current.json').read_text())['path'];ps,_=read_run(path);configs={}
for work in WORKS:
 by={p['name']:p for p in ps if p['workload']==work};eligible=[by[k] for k in ['best_bp','stronger_solver','multi_candidate','adaptive_radius','best_combined']];minimum=min(p['failures'] for p in eligible);winner=min([p for p in eligible if p['failures']<=1.1*minimum],key=lambda p:p['mean_ms'])
 configs[work]=[by['original']['config'],dict(winner['config'],name='selected_combined')]
p=run(configs,'orchestration_memory_smoke',count=8,mode='memory',wall_cap=120,point_cap=45)
led=json.loads((p/'EXECUTION_LEDGER.json').read_text());assert all(j['status']=='COMPLETE' and j['scope']=='instrumented_full_corpus_memory_not_publication_latency' for j in led)
for j in led:
 audit=json.loads((pathlib.Path(j['directory'])/'memory.json').read_text());assert len(audit['allocation_counts'])==8 and len(audit['soak'])==2 and audit['native_capacity'];assert all(q['independent_shots']==q['repeated_shots']==8 for q in audit['soak'])
# Confirmatory access is rejected before labels open when the lock is absent.
d=ROOT/'evidence/unfrozen_access_smoke';d.mkdir(exist_ok=True);job=dict(workload=WORKS[0],config=configs[WORKS[0]][0],directory=str(d),split='confirmatory',count=8,mode='accuracy');atomic(d/'job.json',job);worker(d/'job.json');assert json.loads((d/'summary.json').read_text())['status']=='ERROR' and not (d/'truth_access.json').exists()
# A deliberately tiny parent budget preserves all missing job records.
p2=run(configs,'watchdog_smoke',count=8,mode='validation',wall_cap=.001,point_cap=.001);assert all(j['status']=='DECODE_TIMEOUT' for j in json.loads((p2/'EXECUTION_LEDGER.json').read_text()))
atomic(ROOT/'evidence/orchestration_smoke.json',dict(status='PASS',memory_run=str(p.relative_to(ROOT)),watchdog_run=str(p2.relative_to(ROOT)),unfrozen_access_rejected=True))
print('PASS memory instrumentation, explicit memory scope, truth guard, and missing-job watchdog')
