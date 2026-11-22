import json,os,sys
from seamwise_bench.runner import launch_worker

def test_memory_timeout_preserves_committed_decode(tmp_path):
    job=dict(directory=str(tmp_path),job_id='fixture',workload='fixture',backend={'name':'fixture'},count=2,budgets={'preparation':2,'decode':2,'memory':.1})
    code='''import json,time,pathlib
p=pathlib.Path(PATH)
(p/'decode_summary.json').write_text(json.dumps({'status':'COMPLETE','job_id':'fixture','requested':2,'completed':2}))
(p/'shots.jsonl').write_text('{}\\n{}\\n')
(p/'stage.json').write_text(json.dumps({'stage':'memory','started_monotonic':time.monotonic(),'budget_s':.1}))
time.sleep(5)
'''.replace('PATH',repr(str(tmp_path)))
    with (tmp_path/'log').open('w') as log:result=launch_worker(job,log,os.environ.copy(),[sys.executable,'-c',code])
    assert result['status']=='MEMORY_AUDIT_FAILED' and result['completed']==2 and result['missing']==0
    assert json.loads((tmp_path/'decode_summary.json').read_text())['status']=='COMPLETE'
    assert len((tmp_path/'shots.jsonl').read_text().splitlines())==2
