"""Isolated replay; never overwrite the delivered experiment or call it new evidence."""
import argparse,pathlib,shutil,subprocess,sys,json,os,time,hashlib
HERE=pathlib.Path(__file__).resolve().parents[1];BASE=HERE.parent/'seamwise_bench'
p=argparse.ArgumentParser();p.add_argument('--destination',required=True);args=p.parse_args();dst=pathlib.Path(args.destination).expanduser().absolute()
if dst.exists():raise RuntimeError('Destination must not exist')
if dst.name!='seamwise_accuracy':raise RuntimeError('Use a destination named seamwise_accuracy with its own parent directory')
dst.parent.mkdir(parents=True,exist_ok=True);sibling=dst.parent/'seamwise_bench'
if sibling.exists():raise RuntimeError('Sibling dependency path must not already exist')
sibling.symlink_to(BASE,target_is_directory=True);dst.mkdir()
for name in ['cpp','python','scripts','configs','tests']:shutil.copytree(HERE/name,dst/name,ignore=shutil.ignore_patterns('__pycache__'))
for name in ['new_samples','prepared_pools']:shutil.copytree(HERE/'results'/name,dst/'results'/name)
shutil.copy2(HERE/'README.md',dst/'README.md');(dst/'evidence').mkdir();shutil.copy2(HERE/'evidence/requirements_accuracy.lock',dst/'evidence/requirements_accuracy.lock')
exe=str(BASE/'.venv/bin/python');env=dict(os.environ,ACCURACY_NATIVE_BUILD='build_prod',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
def run(cmd):subprocess.run(cmd,check=True,cwd=dst.parent,env=env)
run(['cmake','-S',str(dst),'-B',str(dst/'build_prod'),'-DCMAKE_BUILD_TYPE=Release','-DPython_EXECUTABLE='+exe]);run(['cmake','--build',str(dst/'build_prod'),'--parallel','1'])
run([exe,'-m','pytest',str(dst/'tests'),'-q'])
run(['cmake','-S',str(dst),'-B',str(dst/'build_sanitize'),'-DCMAKE_BUILD_TYPE=RelWithDebInfo','-DACCURACY_SANITIZE=ON','-DPython_EXECUTABLE='+exe]);run(['cmake','--build',str(dst/'build_sanitize'),'--target','accuracy_tests','--parallel','1'])
subprocess.run([str(dst/'build_sanitize/accuracy_tests')],check=True,env=dict(env,ASAN_OPTIONS='detect_leaks=1',UBSAN_OPTIONS='halt_on_error=1'))
# Preserve the original lock alongside the explicitly local reproduction lock.
old=json.loads((dst/'configs/confirmatory_lock.json').read_text());shutil.copy2(dst/'configs/confirmatory_lock.json',dst/'configs/original_confirmatory_lock.json')
code="""import sys,pathlib,json,time
sys.path.insert(0,str(pathlib.Path.cwd()/'seamwise_accuracy/python'))
from common import *
from seamwise_bench.audit import environment
p=ROOT/'configs/confirmatory_lock.json';lock=json.loads(p.read_text());original=sha(p)
for name,h in lock['sources'].items():assert sha(ROOT/name)==h,'Source mismatch: '+name
lock['status']='REPRODUCTION_ON_PREVIOUSLY_INSPECTED_SAMPLES';lock['original_lock_sha256']=original;lock['native_module_sha256']=sha(next((ROOT/'build_prod').glob('_accuracy_native*.so')));lock['old_native_module_sha256']=sha(next((OLD/'build').glob('_native*.so')));snapshot=environment();lock['runtime_provenance']={k:snapshot[k] for k in ['versions','binary_sha256','commits']};lock['reproduction_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());atomic(p,lock)
"""
run([exe,'-c',code]);run([exe,str(dst/'scripts/run_confirmatory.py')]);print('Replay completed in',dst,'; this is not new confirmatory evidence.')
