import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from runner import run
cfg={w:[dict(name='bp_iter60',kind='new',policy='repair2' if w.startswith('bb') else 'repair1',scale=.625,iterations=60),dict(name='bp_norm08_30',kind='new',policy='repair2' if w.startswith('bb') else 'repair1',scale=.8,iterations=30)] for w in WORKS}
atomic(ROOT/'configs/P2_control_amendment.json',dict(reason='Isolate iteration from normalization and bit-serial scheduling, which were coupled in the initial fixed presets. Validation-only extension before confirmatory labels are opened.',count=128,configs=cfg))
p=run(cfg,'P2_controls',128,wall_cap=300,point_cap=120);atomic(ROOT/'results/P2_controls_current.json',dict(path=str(p.relative_to(ROOT))))
