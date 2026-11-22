"""Frozen, seeded experiment runner with shot-level outputs and timing traces."""
from __future__ import annotations
import argparse,csv,gc,hashlib,importlib.metadata,json,os,platform,time
from pathlib import Path
import numpy as np
from scipy import sparse
from models import save_model
from decoders import Stack,method_grid,COMMON,ENGINE_OPTIONS

def configurations():
    models=[]
    for d in [3,5,7]:
        for p in [.001,.003,.006]:
            shots=512 if d==3 else 1024 if d==5 and p==.003 else 256 if d==5 else 64
            models.append(dict(id=f'surface_d{d}_p{p:.3f}_B4',family='surface',
                distance=d,rounds=d,p=p,blocks=4,shots=shots))
    for n in [72,144]:
        for p in [.005,.015]:
            models.append(dict(id=f'bb{n}_p{p:.3f}_B4',family='bb',n=n,
                rounds=6,p=p,blocks=4,shots=128))
    for d,shots in [(3,256),(5,64)]:
        models.append(dict(id=f'surface_d{d}_p0.003_B8',family='surface',
            distance=d,rounds=d,p=.003,blocks=8,shots=shots))
    return models

CONTRASTS=[('BF_cut','BF_repair1'),('BF_cut','BF_halo1'),
 ('BF_repair1','BF_repair2'),('LSD2_joint','BF_repair2'),
 ('LSD2_cut','LSD2_repair1'),('OSD0_cut','OSD0_repair1'),
 ('BF_joint','LSD2_joint'),('LSD2_joint','OSD0_joint'),
 ('LSD0_cut','LSD0_repair1')]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def freeze(root):
    conf=dict(schema=2,models=configurations(),methods=method_grid(),
        contrasts=CONTRASTS,correction_family='All planned contrasts across all 15 models',
        sampling_seed_base=734202611,order_seed_base=891202611,
        warmups_per_method=3,core_width=2,
        strict_acceptance_tolerance=1e-10,main_stopping='fixed sample count',
        primary_timing='decode plus wrapper, per shot; compilation and final audit excluded',
        common=COMMON,engines={k:ENGINE_OPTIONS[k] for k in ['BF','LSD0','LSD2','OSD0']},
        pilot='Separate eight-shot seeds used only for runtime allocation; OSD2 omitted from main grid for cost',
        source_hashes={p.name:sha(p) for p in Path(__file__).parent.glob('*.py')})
    path=root/'protocol.json'
    if path.exists():
        existing=json.loads(path.read_text())
        if existing!=conf:raise RuntimeError('Frozen protocol changed')
    else:path.write_text(json.dumps(conf,indent=2)+'\n')
    return conf

def environment():
    packages=['stim','ldpc','numpy','scipy','psutil','pymatching']
    env=dict(python=platform.python_version(),platform=platform.platform(),
       cpu_count=os.cpu_count(),affinity=sorted(os.sched_getaffinity(0)),
       packages={k:importlib.metadata.version(k) for k in packages},
       thread_env={k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']})
    env['cpu_model']=next((v.split(':',1)[1].strip() for v in Path('/proc/cpuinfo').read_text().splitlines() if v.startswith('model name')),'unknown')
    for name in ['cpu.max','memory.max']:
        p=Path('/sys/fs/cgroup')/name
        if p.exists():env[name]=p.read_text().strip()
    return env

def run_model(root,config,index,protocol):
    name=config['id'];path=root/'data'/name;path.mkdir(parents=True,exist_ok=True)
    if (path/'complete.json').exists():
        print('SKIP completed',name,flush=True);return
    shots=config['shots'];seed=protocol['sampling_seed_base']+index
    clean={k:v for k,v in config.items() if k not in ['id','shots']}
    meta=save_model(path,clean,shots,seed)
    d=sparse.load_npz(path/'D.npz');l=sparse.load_npz(path/'L.npz')
    arr=np.load(path/'metadata_arrays.npz');samples=np.load(path/'samples.npz')
    synd=samples['detectors'].astype(np.uint8);truth=samples['observables'].astype(np.uint8)
    grid=method_grid();methods=[a+'_'+b for a,b in grid]
    stacks={};compile_stats=[]
    for engine in ['BF','LSD0','LSD2','OSD0']:
        started=time.perf_counter()
        st=Stack(d,l,arr['p'],arr['detector_blocks'],config['blocks'],engine)
        st.prepare([p for e,p in grid if e==engine]);stacks[engine]=st
        compile_stats.append(dict(engine=engine,seconds=time.perf_counter()-started))
    ranks=[]
    for radius in [1,2]:
        for seam,w in stacks['BF'].prepare_repair(radius):
            ranks.append(dict(seam=seam,radius=radius,columns=len(w.columns),
                              rows=len(w.rows),detector_rank=w.detector_rank,rho=w.rho))
    (path/'ranks.json').write_text(json.dumps(ranks,indent=2)+'\n')
    (path/'compilation.json').write_text(json.dumps(compile_stats,indent=2)+'\n')
    for engine,policy in grid:
        for i in range(3):stacks[engine].decode(synd[i%shots],policy)
    predictions=np.zeros((len(grid),shots,l.shape[0]),dtype=np.uint8)
    consistent=np.zeros((len(grid),shots),dtype=bool)
    failures=np.zeros_like(consistent);fallback=np.zeros_like(consistent)
    timings=np.zeros((len(grid),shots),dtype=np.int64)
    accepted=np.zeros((len(grid),shots),dtype=np.int16)
    changed=np.zeros_like(accepted);skipped=np.zeros_like(accepted)
    rng=np.random.default_rng(protocol['order_seed_base']+index)
    rows=[];events_path=path/'repair_events.csv'
    event_fields=['shot','method','seam','radius','rho','accepted','skipped',
                  'candidate_consistent','cost_drop','logical_changed','failure_before','failure_after']
    begin=time.perf_counter()
    with events_path.open('w',newline='') as ef:
        ew=csv.DictWriter(ef,fieldnames=event_fields);ew.writeheader()
        for shot in range(shots):
            for j in rng.permutation(len(grid)):
                engine,policy=grid[j];method=methods[j]
                tic=time.perf_counter_ns()
                x,fb,events=stacks[engine].decode(synd[shot],policy)
                elapsed=time.perf_counter_ns()-tic
                valid=np.array_equal(d@x%2,synd[shot]);pred=(l@x%2).astype(np.uint8)
                fail=(not valid) or np.any(pred!=truth[shot])
                predictions[j,shot]=pred;consistent[j,shot]=valid
                failures[j,shot]=fail;fallback[j,shot]=fb;timings[j,shot]=elapsed
                accepted[j,shot]=sum(v['accepted'] for v in events)
                changed[j,shot]=sum(not np.array_equal(v['before'],v['after']) for v in events)
                skipped[j,shot]=sum(v['skipped'] for v in events)
                rows.append([shot,method,int(fail),int(valid),int(fb),int(elapsed),
                             int(accepted[j,shot]),int(changed[j,shot]),int(skipped[j,shot])])
                for v in events:
                    ew.writerow(dict(shot=shot,method=method,seam=v['seam'],radius=v['radius'],
                         rho=v['rho'],accepted=int(v['accepted']),skipped=int(v['skipped']),
                         candidate_consistent=int(v['consistent']),cost_drop=f"{v['cost_drop']:.12g}",
                         logical_changed=int(not np.array_equal(v['before'],v['after'])),
                         failure_before=int(np.any(v['before']!=truth[shot])),
                         failure_after=int(np.any(v['after']!=truth[shot]))))
            if (shot+1)%32==0:
                print(name,f'{shot+1}/{shots}',f'{time.perf_counter()-begin:.1f}s',flush=True)
    np.savez_compressed(path/'outcomes.npz',methods=np.array(methods),predictions=predictions,
        failures=failures,consistent=consistent,fallback=fallback,latency_ns=timings,
        accepted=accepted,logical_changes=changed,skipped=skipped)
    with (path/'shots.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['shot','method','failure','consistent','fallback','latency_ns',
                                  'accepted','logical_changes','skipped']);w.writerows(rows)
    # Rank screening must preserve logical outputs for this disjoint single pass.
    a=methods.index('BF_repair1');b=methods.index('BF_rank1')
    assert np.array_equal(predictions[a],predictions[b])
    assert consistent.all()
    complete=dict(id=name,shots=shots,method_count=len(grid),all_consistent=bool(consistent.all()),
          wall_seconds=time.perf_counter()-begin,files={p.name:sha(p) for p in path.iterdir() if p.is_file()})
    (path/'complete.json').write_text(json.dumps(complete,indent=2)+'\n')
    print('DONE',name,'counts',dict(zip(methods,failures.sum(axis=1).tolist())),flush=True)
    del stacks;gc.collect()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument('--only',default='');args=ap.parse_args();root=args.root
    root.mkdir(parents=True,exist_ok=True);protocol=freeze(root)
    (root/'environment.json').write_text(json.dumps(environment(),indent=2)+'\n')
    for i,config in enumerate(protocol['models']):
        if args.only and args.only not in config['id']:continue
        run_model(root,config,i,protocol)

if __name__=='__main__':main()
