"""Lock choices and fixed sample counts from validation throughput only."""
import sys,pathlib,json,math,copy,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from analysis import read_run,save_analysis
lockpath=ROOT/'configs/confirmatory_lock.json'
if lockpath.exists():raise RuntimeError('Confirmatory policy lock already exists')
val=ROOT/json.loads((ROOT/'results/finalists_current.json').read_text())['path'];analysis=save_analysis(val);points,_=read_run(val);matrices={};primary={};components={};timing={};memory={};allconfig={};summary={};primary_unit_s=0;secondary_s=0;timing_s=0;memory_s=0
for work in WORKS:
 ps=[p for p in points if p['workload']==work and not p['invalid']];by={p['name']:p for p in ps}
 eligible=[p for p in ps if p['config'].get('kind','new')=='new' and p['name'] in ['best_bp','stronger_solver','multi_candidate','adaptive_radius','best_combined']];assert eligible
 minimum=min(p['failures'] for p in eligible);accuracy_band=[p for p in eligible if p['failures']<=1.10*minimum];winner=min(accuracy_band,key=lambda p:(p['mean_ms'],p['failures']));selected=dict(winner['config'],name='selected_combined');original=dict(by['original']['config']);tess=dict(by['baseline_tesseract']['config']);external=[p for p in ps if p['name'].startswith('baseline_')];reference=min(external,key=lambda p:(p['failures'],p['mean_ms']));refcfg=dict(reference['config'])
 configs=[original,selected,tess]
 if reference['name']!='baseline_tesseract':configs.append(refcfg)
 primary[work]=configs
 # Fixed secondary 2000 IDs compare components/strong external families.
 supplement=[]
 for name in ['best_bp','stronger_solver','multi_candidate','adaptive_radius']:
  if name in by:supplement.append(dict(by[name]['config']))
 joint=dict(selected,name='matched_joint',joint=True,adaptive=False,radius=2)
 if not joint.get('candidate'):joint['policy']='joint'
 cut={k:v for k,v in dict(selected,name='matched_cut',policy='cut').items() if k not in ['candidate','adaptive','ensemble','joint','radius','K','selection','depth','max_calls']}
 supplement += [joint,cut]
 plain={k:v for k,v in selected.items() if k not in ['candidate','adaptive','ensemble','joint','radius','K','selection','depth','max_calls']}
 for name,policy in [('same_BP_fixed_radius','repair2' if work.startswith('bb') else 'repair1'),('same_BP_radius2','repair2'),('same_BP_joint','joint')]:supplement.append(dict(plain,name=name,policy=policy))
 # Uniform stronger-inner-family controls distinguish architecture from replacement.
 strong_cfg=by['stronger_solver']['config'];family=strong_cfg['band_family']
 for name,policy in [('strong_joint','joint'),('strong_cut','cut'),('strong_all_repair',strong_cfg['policy'])]:
  uniform=dict(strong_cfg,name=name,family=family,iterations=strong_cfg.get('band_iterations',60),order=strong_cfg.get('band_order',2),policy=policy)
  for key in ['band_family','band_iterations','band_order']:uniform.pop(key,None)
  supplement.append(uniform)
 for name in ['baseline_lsd','baseline_osd','baseline_relay','baseline_gari']:
  if name in by and name not in {c['name'] for c in configs}:supplement.append(dict(by[name]['config']))
 components[work]=supplement
 base_time={p['name']:p['mean_ms']/1000 for p in ps};mean_sel=winner['mean_ms']/1000
 primary_unit_s+=sum(mean_sel if c['name']=='selected_combined' else base_time[c['name']] for c in configs)
 def forecast_secondary(c):
  if c['name'].startswith('strong_'):return max(base_time.get('baseline_lsd',0),base_time.get('stronger_solver',0),.001)
  if c['name'] in ['matched_joint','matched_cut']:return max(base_time.get(c['name'],0),2*mean_sel)
  return base_time.get(c['name'],max(mean_sel,.001))
 secondary_s+=2000*sum(forecast_secondary(c) for c in supplement)
 # Timing corpus remains independent; baseline test-pass runtime also retained.
 t=[original,selected]
 validation_point_target=winner['failures']<=1.1*reference['failures']
 if validation_point_target:t.append(refcfg)
 timing[work]=t;timing_s+=3*1024*sum(mean_sel if c['name']=='selected_combined' else base_time[c['name']] for c in t)
 memory[work]=[original,selected];memory_s+=512*5*(mean_sel+base_time['original'])
 summary[work]=dict(selected_source_role=winner['name'],selected_failures=winner['failures'],minimum_Seamwise_validation_failures=minimum,selection_rule='fastest within 10% of minimum observed Seamwise validation failure count; an operating-point rule, not an internal noninferiority confidence claim',n_validation=winner['n'],selected_mean_ms=winner['mean_ms'],reference=reference['name'],reference_validation_failures=reference['failures'],tesseract_validation_failures=by['baseline_tesseract']['failures'],validation_point_target=validation_point_target)
 allconfig[work]=configs+supplement
# Reserve tail/I/O contingency and explicit postprocessing/memory scope.
reserved=secondary_s+timing_s+memory_s+300
possible=[]
for n in [10000,8000,5000,2000]:
 estimate=reserved+n*primary_unit_s
 if estimate<=.85*5*3600:possible.append((n,estimate))
N,forecast=possible[0] if possible else (2000,reserved+2000*primary_unit_s)
planned_pairs=sum(len({c['name'] for c in cs})*(len({c['name'] for c in cs})-1)//2 for cs in allconfig.values())
sources={str(p.relative_to(ROOT)):sha(p) for base in ['cpp','python'] for p in (ROOT/base).rglob('*') if p.is_file() and p.suffix in ['.cpp','.hpp','.py']}
from seamwise_bench.audit import environment
runtime_provenance=environment()
freeze=dict(created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),status='FROZEN_BEFORE_CONFIRMATORY_ACCESS',primary_count=N,secondary_count=2000,timing_count=1024,timing_repetitions=3,memory_count=512,memory_scope='full 512-ID validation corpus, two independent/repeated-syndrome soak cycles; separate instrumentation',max_wall_s=5*3600,primary_configs=primary,secondary_configs=components,timing_configs=timing,memory_configs=memory,selection=summary,planned_comparisons=planned_pairs,noninferiority_margin=.10,
 N_rule='largest of 10000/8000/5000/2000 whose validation-only mean forecast plus fixed secondary/timing/memory reservations fits 85% of five-hour cap; never shortened after outcomes',forecast_s=forecast,forecast_components=dict(primary_seconds_per_shot_across_matrix=primary_unit_s,secondary_s=secondary_s,timing_s=timing_s,memory_s=memory_s,reserved_s=reserved),
 sources=sources,runtime_provenance={key:runtime_provenance[key] for key in ['versions','binary_sha256','commits']},native_module_sha256=sha(next((ROOT/'build_prod').glob('_accuracy_native*.so'))),new_dataset_manifest_sha256=sha(ROOT/'results/new_samples/manifest.json'),pool_manifest_sha256=sha(ROOT/'results/prepared_pools/manifest.json'),old_native_module_sha256=sha(next((OLD/'build').glob('_native*.so'))),previous_test_status='EXPLORATORY_ONLY',first_confirmatory_access=None)
atomic(lockpath,freeze);ledger('P4 independent confirmatory policy/data lock','COMPLETE',fixed_N=N,forecast_s=forecast,selection=summary);print(json.dumps(dict(N=N,forecast_hours=forecast/3600,selection=summary),indent=2))
