#!/usr/bin/env python3
import sys,pathlib,json,time,hashlib,signal
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from seamwise_bench.common import ROOT,HIST,load_model,atomic,unique_run,pin,sha
from seamwise_bench.adapters import make

def main():
    pin();out=unique_run('historical-regression');records=[];started=time.monotonic()
    names=sorted(p.name for p in (HIST/'data').iterdir())
    first=['surface_d5_p0.006_B4','bb144_p0.015_B4']
    for name in first+[n for n in names if n not in first]:
        a=load_model(name);raw=np.load(a['path']/'samples.npz')
        for engine,family,persistent in [('BPHUF','bphuf',False),('BPSW','bphuf',True),('HUF','huf',False),('SW','huf',True)]:
            archive=HIST/'results'/(name+'__'+engine+'.npz')
            rec=dict(model=name,engine=engine,input_sha256=sha(a['path']/'samples.npz'),independent_accuracy_samples=0)
            if not archive.exists():records.append(dict(rec,status='UNAVAILABLE_HISTORICAL_OUTPUT'));continue
            if time.monotonic()-started>600:records.append(dict(rec,status='DEFERRED_CORRECTNESS_BUDGET'));continue
            old=np.load(archive);expected=old['corrections'];backend=make(a,dict(kind='native',family=family,persistent=persistent,policy='repair1'))
            failures=0;valid=True;matches=True
            for i,s in enumerate(raw['detectors'][:len(expected)]):
                frame,x=backend.decode(s.astype(np.uint8));matches &= np.array_equal(np.packbits(x,bitorder='little'),expected[i]);valid &= np.array_equal(a['d']@x%2,s);failures+=int(np.any(frame!=raw['observables'][i]))
                if not matches or not valid:raise AssertionError((name,engine,i))
            records.append(dict(rec,status='PASS',shots=len(expected),exact_corrections=True,syndrome_valid=True,failures=failures))
            atomic(out/'regression.json',records)
    atomic(out/'regression.json',records);print(out)

if __name__=='__main__':main()
