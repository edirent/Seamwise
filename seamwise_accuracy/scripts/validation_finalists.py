import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from analysis import read_run
from runner import run
points=[]
for name in ['P2_current.json','P2_controls_current.json','P3_current.json','P3_controls_current.json']:
 points+=read_run(ROOT/json.loads((ROOT/'results'/name).read_text())['path'])[0]
configs={};roles={}
for work in WORKS:
 ps=[p for p in points if p['workload']==work and not p['invalid']];new=[p for p in ps if p['config'].get('kind','new')=='new']
 def choose(candidates):return min(candidates,key=lambda p:(p['failures'],p['mean_ms']))['config']
 best_bp=json.loads((ROOT/'configs/P2_selected.json').read_text())[work]['best']
 strong=choose([p for p in new if p['config'].get('band_family')])
 multi=choose([p for p in new if p['name'].startswith('K') and p['config'].get('K',1)>1])
 adaptive=choose([p for p in new if p['config'].get('adaptive')])
 complete=choose([p for p in new if p['config'].get('policy') not in ['joint','cut'] and not p['config'].get('joint')])
 r=dict(original=dict(name='original',kind='original',family='bphuf',persistent=True,policy='repair2' if work.startswith('bb') else 'repair1'),bp=dict(best_bp,name='best_bp'),stronger=dict(strong,name='stronger_solver'),multi=dict(multi,name='multi_candidate'),adaptive=dict(adaptive,name='adaptive_radius'),combined=dict(complete,name='best_combined'))
 joint=dict(complete,name='matched_joint',joint=True,adaptive=False,radius=2)
 if not joint.get('candidate'):joint['policy']='joint'
 r['matched_joint']=joint;r['matched_cut']={k:v for k,v in dict(complete,name='matched_cut',policy='cut').items() if k not in ['candidate','adaptive','ensemble','joint','radius','K','selection','depth','max_calls']}
 # External points were validation-selected before this task's confirmatory data.
 for p in ps:
  if p['name'].startswith('baseline_'):r[p['name']]=dict(p['config'])
 configs[work]=list(r.values());roles[work]={key:value['name'] for key,value in r.items()}
atomic(ROOT/'configs/finalist_selection.json',dict(configs=configs,roles=roles,scope='128-shot prescreen, minimum validation failures then latency; every retained role is re-evaluated on all 512 validation IDs before final policy lock',wall_cap=1800,point_cap=700))
p=run(configs,'validation_finalists',512,wall_cap=1800,point_cap=700);atomic(ROOT/'results/finalists_current.json',dict(path=str(p.relative_to(ROOT))))
