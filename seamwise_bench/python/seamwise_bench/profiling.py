import json
import pathlib
import subprocess
import os
import numpy as np
from .common import ROOT,atomic,unique_run,load_model,pin
from .adapters import supports,make
from .datasets import verify_manifest,frozen_model

def export_native(path,model,shots,persistent=True,family='bphuf',policy='repair1'):
    d=model['d'];p=model['p'];w=np.log((1-p)/p)
    with pathlib.Path(path).open('x') as f:
        f.write(f"SWB1 {d.shape[0]} {d.shape[1]} {model['l'].shape[0]} {model['meta']['blocks']} {len(shots)} {family} {int(persistent)} {policy}\n")
        f.write(' '.join(map(repr,p.tolist()))+'\n');f.write(' '.join(map(repr,w.tolist()))+'\n');f.write(' '.join(map(str,model['labels']))+'\n')
        for ds,ls in zip(supports(d),supports(model['l'])):f.write(' '.join(map(str,[len(ds)]+ds+[len(ls)]+ls))+'\n')
        for s in shots:f.write(' '.join(map(str,s.astype(int)))+'\n')

def profile(manifestpath,count=32):
    pin();v=verify_manifest(manifestpath);out=unique_run('profiles');records=[]
    for name,item in v['workloads'].items():
        a=frozen_model(item);ss=np.load(ROOT/item['splits']['validation']['path'])['detectors'][:count]
        for persistent in [False,True]:
            label=name+('_persistent' if persistent else '_rebuild')
            b=make(a,dict(kind='native',family='bphuf',policy='repair1',persistent=persistent),audit=True)
            shot_diagnostics=[];before=b.backend.diagnostics()
            for idx,s in enumerate(ss):
                b.decode(s);after=b.backend.diagnostics();histories=[]
                for previous,current in zip(before['solvers'],after['solvers']):histories+=current['histories'][len(previous['histories']):]
                peak=lambda key:max((max(h.get(key,[]),default=0) for h in histories),default=0)
                counters={key:sum(so['counts'].get(key,0) for so in after['solvers'])-sum(so['counts'].get(key,0) for so in before['solvers']) for key in after['solvers'][0]['counts']}
                shot_diagnostics.append(dict(sample_id=item['splits']['validation']['sample_id_prefix']+':'+str(idx),largest_vertices=peak('merge_sizes'),largest_detectors=peak('merge_detectors'),largest_faults=peak('merge_faults'),largest_incidences=peak('merge_incidences'),largest_rank=peak('final_ranks'),failed_local_calls=sum(not h['success'] for h in histories),operation_counts=counters,
                                             wrapper_counts={key:after['wrapper'][key]-before['wrapper'][key] for key in after['wrapper']}))
                before=after
            atomic(out/(label+'_per_shot.json'),shot_diagnostics)
            diagnostic=b.backend.diagnostics();atomic(out/(label+'_diagnostics.json'),diagnostic)
            data=out/(label+'.swb');export_native(data,a,ss,persistent)
            if (ROOT/'build_gprof/native_runner').exists():
                env=os.environ.copy();env['GMON_OUT_PREFIX']=str(out/(label+'.gmon'))
                with (out/(label+'_native.jsonl')).open('x') as stdout,(out/(label+'_native.stderr')).open('x') as stderr:
                    r=subprocess.run([str(ROOT/'build_gprof/native_runner'),str(data)],stdout=stdout,stderr=stderr,env=env,timeout=120)
                for gmon in out.glob(label+'.gmon.*'):
                    text=subprocess.check_output(['gprof',str(ROOT/'build_gprof/native_runner'),str(gmon)],text=True)
                    (out/(label+'_gprof.txt')).write_text(text)
            sizes=[size for so in diagnostic['solvers'] for h in so['histories'] for size in h['merge_sizes']]
            records.append(dict(model=name,persistent=persistent,shots=len(ss),histories_include_infeasible=True,
                         cluster_denominator='one observation per actual merge, including failed local calls; not independent shots',
                         merge_size_quantiles=np.quantile(sizes,[.5,.95,.99,1]).tolist() if sizes else [],
                         wrapper=diagnostic['wrapper'],solver_counts=[s['counts'] for s in diagnostic['solvers']]))
    atomic(out/'profile_summary.json',records);plots(out,records);print(out);return out

def plots(out,records):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for p in out.glob('*_diagnostics.json'):
        d=json.loads(p.read_text());clusters=[z for s in d['solvers'] for h in s['histories'] for z in h['merge_sizes']]
        per_shot=[max(h['merge_sizes'],default=0) for s in d['solvers'] for h in s['histories']]
        fig,ax=plt.subplots()
        for label,vals in [('per merge',clusters),('per local solve peak (BP exits=0)',per_shot)]:
            if vals:
                vals=np.sort(vals);ax.step(vals,np.arange(1,len(vals)+1)/len(vals),label=label)
        ax.set(xlabel='Detector + fault vertices',ylabel='CDF',title=p.stem);ax.legend(fontsize=7);fig.tight_layout();fig.savefig(out/(p.stem+'_clusters.png'),dpi=140);plt.close(fig)

if __name__=='__main__':
    import sys
    profile(sys.argv[1])
