"""Staged scaling registry, with extraction and logical depth kept distinct."""
import ast
import inspect
import json
import pathlib
import time
import numpy as np
from scipy import sparse
import stim
from .common import ROOT,HIST,sha,atomic,unique_run

def build_circuit(config):
    import models
    # Extend the recovered generator at its single logical-gate loop; preserve
    # all stabilizer-history propagation and noise instructions verbatim.
    tree=ast.parse(inspect.getsource(models.build_circuit))
    class SeparateDepth(ast.NodeTransformer):
        def visit_For(self,node):
            self.generic_visit(node)
            if isinstance(node.iter,ast.Call) and isinstance(node.iter.func,ast.Name) and node.iter.func.id=='gate_pairs':
                node.iter.args[1]=ast.Name(id='_logical_layer',ctx=ast.Load())
                iterator=ast.parse("range(t * config.get('gate_layers', rounds) // rounds, (t+1) * config.get('gate_layers', rounds) // rounds)",mode='eval').body
                return ast.For(target=ast.Name(id='_logical_layer',ctx=ast.Store()),iter=iterator,body=[node],orelse=[])
            return node
    tree=SeparateDepth().visit(tree);ast.fix_missing_locations(tree);namespace=dict(vars(models));exec(compile(tree,'<seamwise_extended_generator>','exec'),namespace)
    return namespace['build_circuit'](config)

def registry():
    entries=[]
    def add(axis,cfg,label):entries.append(dict(axis=axis,config=cfg,label=label,status='REGISTERED_NOT_RUN'))
    base=dict(family='surface',distance=3,blocks=4,rounds=3,p=.003,gate_layers=3)
    for b in [2,4,8,16,32,64]:add('blocks',dict(base,blocks=b),f'B{b}')
    for d in [3,5,7,9,11,15]:add('distance_fixed_T',dict(base,distance=d),f'd{d}_T3')
    for t in [3,6,12,24]:add('extraction_fixed_logical_layers',dict(base,rounds=t,gate_layers=3),f'T{t}_G3')
    for d in [3,5,7,9,11,15]:
        for ratio in [1,2]:add('physical_depth',dict(base,distance=d,rounds=d*ratio,gate_layers=d*ratio),f'd{d}_T{ratio}d')
    for g in [0,1,2,3,6,12]:add('logical_gate_layers_fixed_T',dict(base,gate_layers=g),f'G{g}_T3')
    for n in [72,144]:
        for p in [.005,.015]:add('published_BB',dict(family='bb',n=n,blocks=4,rounds=6,p=p,gate_layers=6),f'BB{n}_p{p}')
    for p in [.001,.003,.006]:add('surface_noise',dict(base,p=p),f'p{p}')
    for path in sorted((HIST/'data').iterdir()):entries.append(dict(axis='historical_regression_anchor',label=path.name,config=json.loads((path/'model.json').read_text()),status='HISTORICAL_READ_ONLY',model_json_sha256=sha(path/'model.json')))
    return entries

def prepare_scaling(budget_s=300):
    import models
    out=unique_run('scaling');entries=registry();start=time.monotonic();made={}
    # First-stage controlled endpoints and all requested axis values up to
    # declared preparation budget. Physically deep large distances remain
    # stress workloads if that budget expires; no silent matrix deletion.
    for i,e in enumerate(entries):
        if e['axis']=='historical_regression_anchor':continue
        cfg=e['config'];key=json.dumps(cfg,sort_keys=True)
        if key in made:e.update(status='PREPARED_ALIAS',path=made[key]);continue
        if time.monotonic()-start>budget_s:
            e.update(status='DEFERRED_COMPUTE_BUDGET',reason=f'predeclared {budget_s}s model preparation budget');continue
        if cfg.get('distance',0)>=9 and e['axis']=='physical_depth':
            e.update(status='STRESS_ONLY_NOT_PREPARED',reason='large proportional-depth model outside first-stage storage/CPU budget');continue
        try:
            c,dem,d,l,p,labels,spec,gates=build_circuit(cfg)
            # G=T must retain the complete old circuit/noise model exactly.
            if cfg.get('gate_layers')==cfg['rounds']:
                original=models.build_circuit(cfg)
                assert str(c)==str(original[0]) and str(dem)==str(original[1])
            dest=out/f'model_{i:02d}_{e["label"]}';dest.mkdir()
            (dest/'circuit.stim').write_text(str(c)+'\n');(dest/'detector_model.dem').write_text(str(dem)+'\n');sparse.save_npz(dest/'D.npz',d);sparse.save_npz(dest/'L.npz',l)
            np.savez_compressed(dest/'metadata_arrays.npz',p=p,detector_blocks=labels)
            seed=412620261109+i;det,obs=c.compile_detector_sampler(seed=seed).sample(shots=16,separate_observables=True)
            np.savez_compressed(dest/'validation.npz',detectors=det.astype(np.uint8),observables=obs.astype(np.uint8))
            cnot=sum(len(ins.targets_copy())//2 for ins in c.flattened() if ins.name=='CX')
            meta=dict(cfg,detectors=d.shape[0],faults=d.shape[1],incidences=d.nnz,max_row_degree=int(d.getnnz(axis=1).max()),max_column_degree=int(d.getnnz(axis=0).max()),
                      observables=l.shape[0],qubits=c.num_qubits,code_n=spec['n'],code_k=spec['k'],code_d=cfg.get('distance'),
                      distance_provenance='surface construction' if cfg['family']=='surface' else 'BB minimum distance not recomputed',
                      logical_gate_layers=cfg['gate_layers'],extraction_rounds=cfg['rounds'],logical_cnot_pairs=len(gates),physical_CX_count_including_ideal_initialization=cnot,
                      logical_cnots=gates,seed=seed,shots=16,noise_class='circuit_level' if cfg['family']=='surface' else 'phenomenological')
            atomic(dest/'model.json',meta)
            rel=str(dest.relative_to(ROOT));made[key]=rel;e.update(status='PREPARED',path=rel,metadata=meta,hashes={p.name:sha(p) for p in dest.iterdir() if p.is_file()})
        except Exception as ex:e.update(status='ERROR',error=repr(ex))
        atomic(out/'registry.json',entries)
    atomic(out/'registry.json',entries);print(out);return out

if __name__=='__main__':prepare_scaling()
