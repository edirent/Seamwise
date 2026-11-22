"""Wait for sequential benchmarks, then finish fixed-budget recovery and analysis."""
import pathlib,json,time,subprocess,sys,os
root=pathlib.Path(__file__).resolve().parents[1];state=root/'evidence/finish_pipeline.json'
def write(status,**extra):
 tmp=state.with_suffix('.tmp');tmp.write_text(json.dumps(dict(status=status,utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**extra),indent=2)+'\n');os.replace(tmp,state)
if state.exists():raise RuntimeError('A finish pipeline is already recorded')
write('WAITING_FOR_BENCHMARKS')
while True:
 index=json.loads((root/'results/P4_run_index.json').read_text())
 if index['status']!='RUNNING':break
 time.sleep(10)
if index['status']!='COMPLETE':write('STOPPED_FOR_EXECUTION_ERROR',index_status=index['status']);raise SystemExit(1)
steps=[('primary_completion','build_prod','complete_missing_primary.py'),('numeric_audit','build_audit','post_diagnostic_llr.py'),('final_reports','build_prod','finalize_results.py')]
for name,build,script in steps:
 write('RUNNING',step=name);env=dict(os.environ,ACCURACY_NATIVE_BUILD=build,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
 log=root/'evidence'/(name+'.log')
 with log.open('x') as f:r=subprocess.run([sys.executable,str(root/'scripts'/script)],stdout=f,stderr=subprocess.STDOUT,env=env)
 if r.returncode:write('ERROR',step=name,exitcode=r.returncode,log=str(log.relative_to(root)));raise SystemExit(r.returncode)
write('REPORTS_READY_FOR_REVIEW')
