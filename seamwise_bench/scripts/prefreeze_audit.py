#!/usr/bin/env python3
import sys,pathlib,json,hashlib,concurrent.futures,multiprocessing
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from seamwise_bench.common import ROOT,atomic,pin
from seamwise_bench.datasets import verify_manifest,frozen_model
from seamwise_bench.adapters import make
from seamwise_bench.fidelity import compare_model

def native_worker(task):
    manifest,work,cfg=task;pin();item=verify_manifest(manifest)['workloads'][work];m=frozen_model(item)
    ss=np.load(ROOT/item['splits']['validation']['path'])['detectors'][:4]
    b=make(m,cfg)
    return work,[hashlib.sha256(b.decode(s)[1].tobytes()).hexdigest() for s in ss]

def main():
    pin();manifest=ROOT/'results/20261109T191912Z-dataset-43f9bff8/manifest.json';v=verify_manifest(manifest)
    selection=json.loads((ROOT/'evidence/selection_record.json').read_text());records=[];tasks=[]
    out=ROOT/'evidence/prefreeze_reproducers';out.mkdir(exist_ok=True)
    for work,item in v['workloads'].items():
        m=frozen_model(item);m['name']=work;ss=np.load(ROOT/item['splits']['validation']['path'])['detectors'][:4]
        candidate=selection['selected'][work]['candidate'];compare_model(m,ss,[{k:x for k,x in candidate.items() if k not in ['name','kind']}],out)
        configs=[selection['selected'][work]['reference_backend']]
        for family,point in selection['selected'][work]['baselines'].items():
            if point and family!='tesseract':configs.append(point['config'])
        if not any(c['kind']=='relay' for c in configs):configs.append(dict(name='relay_strong_repro',kind='relay',precision='F64',seed=20261109,pre_iter=80,num_sets=100,set_max_iter=60,stop_nconv=5))
        for cfg in configs:
            b=make(m,cfg);expected=[b.decode(s) for s in ss];order=list(reversed(range(len(ss))))
            for i in order:
                frame,x=b.decode(ss[i]);assert np.array_equal(frame,expected[i][0]);assert (x is None and expected[i][1] is None) or np.array_equal(x,expected[i][1])
            fresh=make(m,cfg)
            for i,s in enumerate(ss):
                frame,x=fresh.decode(s);assert np.array_equal(frame,expected[i][0]);assert (x is None and expected[i][1] is None) or np.array_equal(x,expected[i][1])
            records.append(dict(workload=work,config=cfg,shots=4,reversed_and_fresh_exact=True,validity=[None if x is None else bool(np.array_equal(m['d']@x%2,s)) for s,(_,x) in zip(ss,expected)]))
        tasks.extend([(str(manifest),work,candidate)]*2)
    ctx=multiprocessing.get_context('spawn')
    with concurrent.futures.ProcessPoolExecutor(max_workers=2,mp_context=ctx) as pool:results=list(pool.map(native_worker,tasks))
    for i in range(0,len(results),2):assert results[i]==results[i+1]
    atomic(ROOT/'evidence/prefreeze_contract_audit.json',dict(status='PASS',records=records,independent_worker_correction_hashes=results,workers=2,decoder_threads_per_worker=1))
    print('PASS selected-policy oracle, external reset/order, and independent-worker contracts')

if __name__=='__main__':main()
