import sys,pathlib,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from runner import run
configs={}
old_selection=json.loads((OLD/'evidence/selection_record.json').read_text())['selected']
for work in WORKS:
 policy='repair2' if work.startswith('bb') else 'repair1';points=[dict(name='original',kind='original',family='bphuf',persistent=True,policy=policy)]
 for name,scale,it,damping,schedule in [('bp_reference',.625,30,0,'parallel'),('bp_norm08',.8,60,0,'parallel'),('bp_norm10',1.,60,0,'parallel'),('bp_damp08',.8,60,.25,'parallel'),('bp_serial',.625,60,0,'serial'),('bp_norm05',.5,60,0,'parallel')]:points.append(dict(name=name,kind='new',policy=policy,scale=scale,iterations=it,damping=damping,schedule=schedule))
 points.append(dict(name='band_lsd2',kind='new',policy=policy,band_family='lsd',band_iterations=60,band_order=2,iterations=30))
 points.append(dict(name='band_osd0',kind='new',policy=policy,band_family='osd',band_iterations=60,band_order=0,iterations=30))
 if work.startswith('surface_d3'):points.append(dict(name='band_osd2',kind='new',policy=policy,band_family='osd',band_iterations=60,band_order=2,iterations=30))
 for fam in ['tesseract','lsd','osd','relay','gari']:
  point=old_selection[work]['baselines'][fam]
  if point:cfg=dict(point['config']);cfg['name']='baseline_'+fam;points.append(cfg)
  else:
   # Preserve unavailable eligible points explicitly; no invalid baseline defeat.
   points.append(dict(name='baseline_'+fam,kind=fam,deferred='No complete zero-invalid prior operating point. New bounded validation of the recorded strongest effort remains required before inferential comparison.'))
 configs[work]=points
atomic(ROOT/'configs/P2_validation.json',dict(count=128,point_cap=240,wall_cap=1800,configs=configs,design='six fixed BP presets plus fixed stronger-band solvers; no Cartesian grid; external settings inherited from prior validation, never final outcomes'))
if __name__=='__main__':
 p=run(configs,'P2_validation',128,wall_cap=1800,point_cap=240);atomic(ROOT/'results/P2_current.json',dict(path=str(p.relative_to(ROOT))))
