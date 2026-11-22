import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from runner import run
selected=json.loads((ROOT/'configs/P2_selected.json').read_text());cfg={}
for work in WORKS:
 base=selected[work]['best_fast'];cfg[work]=[
  dict(base,name='fixed_r2_K1',candidate=True,K=1,radius=2,selection='cost'),
  dict(base,name='fixed_r2_K8',candidate=True,K=8,radius=2,selection='cost'),
  dict(base,name='joint_fast',policy='joint'),dict(base,name='cut_fast',policy='cut'),
  dict(base,name='joint_search8',candidate=True,K=8,joint=True,policy='joint',selection='cost'),
  dict(base,name='fixed_r1_K8',candidate=True,K=8,radius=1,selection='cost')]
atomic(ROOT/'configs/P3_attribution_controls.json',dict(count=128,configs=cfg,reason='Disentangle global radius/initialization from extra candidate search; joint control reuses its identical primary seed instead of doing a useless second solve.',wall_cap=600))
p=run(cfg,'P3_controls',128,wall_cap=600,point_cap=240);atomic(ROOT/'results/P3_controls_current.json',dict(path=str(p.relative_to(ROOT))))
