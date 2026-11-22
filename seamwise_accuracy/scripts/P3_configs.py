import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from runner import run
assert '6 passed' in (ROOT/'evidence/P3_factory_gate.log').read_text(),'Python/native contract gate failed'
assert json.loads((ROOT/'evidence/P3_final_sanitize_tests.log').read_text())['status']=='PASS','Sanitizer gate failed'
atomic(ROOT/'evidence/P3_gate.json',dict(status='PASS',source_hashes={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'cpp').rglob('*') if p.is_file()},binary_sha256=sha(next((ROOT/'build_prod').glob('_accuracy_native*.so')))))
selected=json.loads((ROOT/'configs/P2_selected.json').read_text());configs={}
for work in WORKS:
 base=selected[work]['best_fast'];points=[dict(base,name='P2_fast'),dict(name='original',kind='original',family='bphuf',persistent=True,policy='repair2' if work.startswith('bb') else 'repair1')]
 for K in [1,2,4,8,16]:
  for selection in ['cost','class_mass']:points.append(dict(base,name=f'K{K}_{selection}',candidate=True,K=K,selection=selection,depth=2,max_calls=2))
 for selection in ['cost','class_mass']:
  points.append(dict(base,name='adaptive8_'+selection,candidate=True,K=8,selection=selection,adaptive=True,radius=1,depth=2,max_calls=2))
  points.append(dict(base,name='ensemble4_'+selection,candidate=True,K=4,selection=selection,ensemble=True,depth=2,max_calls=2))
  if selected[work]['best']!=selected[work]['best_fast']:points.append(dict(selected[work]['best'],name='combined8_'+selection,candidate=True,K=8,selection=selection,depth=2,max_calls=2))
 configs[work]=points
atomic(ROOT/'configs/P3_validation.json',dict(count=128,wall_cap=1200,point_cap=240,configs=configs,design='K1/2/4/8/16 by two selectors at one fixed fast BP preset; adaptive8/ensemble4 targeted controls; only K8 combines the accuracy-oriented BP preset. No Cartesian BP-by-radius-by-K grid.',max_repair_solver_calls=2,generated_attempt_bound_per_band='2+128*(3+K), depth<=2; retained unique configurations <=K+1 including incumbent',stronger_source_tests='P0/P1 candidate coverage plus remaining P2 validation errors justify this bounded stage'))
p=run(configs,'P3_validation',128,wall_cap=1200,point_cap=240);atomic(ROOT/'results/P3_current.json',dict(path=str(p.relative_to(ROOT))))
