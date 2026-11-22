#!/usr/bin/env python3
"""Document unrun cells without changing any preselected policy."""
import sys,pathlib,json,copy
import yaml
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from seamwise_bench.common import ROOT,atomic

def main():
    final=yaml.safe_load((ROOT/'configs/final.yaml').read_text());selection=json.loads((ROOT/'evidence/selection_record.json').read_text());plans=[];chunks=[]
    for work,s in selection['selected'].items():
        for family in ['lsd','osd','relay','gari']:
            point=s['baselines'][family]
            if point is None:
                plans.append(dict(workload=work,family=family,status='VALIDATION_ELIGIBILITY_UNRESOLVED',reason='No complete zero-invalid point in the bounded grid; do not launch publication timing until a new declared validation gate passes.'))
                continue
            cfg=copy.deepcopy(final);cfg['workloads']=[work];name='tuned_'+family
            cfg['backends']=[b for b in final['backends'] if b['name']==name];cfg['deferred_jobs']={};cfg['quality_reference_labels']={};cfg['repetitions']=7
            cfg['campaign_wall_budget_s']=36000;cfg['stage_wall_budgets']=dict(timing=14400,accuracy=14400,memory=3600)
            cfg['budgets']=dict(preparation=120,decode=14400,memory=1800)
            cfg['continuation_scope']='Previously deferred operating point selected from validation before the first final test; no retuning. Extra campaign beyond original completed budget. Same IDs add no independent samples.'
            filename='configs/deferred_'+work+'_'+family+'.yaml';(ROOT/filename).write_text(yaml.safe_dump(cfg,sort_keys=False))
            mean=point['mean_ns'];forecast=dict(accuracy_10000_cpu_h=mean*10000/3.6e12,timing_1024x7_cpu_h=mean*7168/3.6e12,memory_8x1024_cpu_h=mean*8192/3.6e12)
            plans.append(dict(workload=work,family=family,status='PREDECLARED_DEFERRED',config=filename,validation_mean_ns=mean,forecast=forecast))
            chunks.append(f"### {work}: {family}\n\nValidation mean-based forecast: accuracy {forecast['accuracy_10000_cpu_h']:.3f} CPU h; timing {forecast['timing_1024x7_cpu_h']:.3f} CPU h; full memory/soaks about {forecast['memory_8x1024_cpu_h']:.3f} CPU h. Hard-shot tails, preparation and research I/O can increase wall time.\n\n```bash\nscripts/seamwise-bench freeze --config {filename} --manifest results/20261109T191912Z-dataset-43f9bff8/manifest.json\n# Substitute the actual new frozen manifest printed above:\nscripts/run_final results/NEW_FROZEN_CAMPAIGN/manifest.json\n```\n")
    text='# Remaining registered work\n\nRun commands from seamwise_bench/. These are unrun continuations beyond the original campaign budget, not promised completed comparisons. Policies below were selected on validation before final labels opened; do not choose new parameters from the final outcomes. Keep the original planned multiplicity correction and quality target. No new tuning or universal strongest-baseline claim is authorized by these point comparisons alone.\n\n'+'\n'.join(chunks)
    text+='\nRelay/GARI workloads with no valid completed validation point require a newly budgeted validation sweep first. Existing bounded grid, nonconvergence reproducers, and unlaunched trials are preserved. Rerun the full recorded validation matrix with a larger predeclared wall cap in a new config; do not use test labels to select effort.\n\nLarge d=9/11/15, T=d/2d stress fixtures were registered but not prepared. Their circuit generation/decode CPU demand has no defensible measured throughput estimate; report UNAVAILABLE rather than extrapolate a near-linear law. To prepare after allocating a new storage/CPU budget, run `PYTHONPATH=python .venv/bin/python -m seamwise_bench.scaling`; the present first-stage implementation deliberately keeps these large proportional-depth cells stress-only, so enabling them requires an explicit new registry/budget revision and model-equivalence gates.\n'
    (ROOT/'REMAINING.md').write_text(text);atomic(ROOT/'evidence/deferred_work_plan.json',plans)
    matrix=[]
    for name,status,validity,source in [('native_Seamwise','AVAILABLE','D x = s outside timing','C++20, exact Python-reference fidelity'),('HUF_original_author_executable','UNAVAILABLE','UNAVAILABLE','Official executable not located'),('HUF_reference','REFERENCE_REIMPLEMENTATION','D x = s outside timing','Recovered Python reference and fidelity native port'),('Tesseract','AVAILABLE','UNAVAILABLE: observable-only API','Official pinned opt source, 2026 optimization lineage verified'),('BP_LSD','AVAILABLE','D x = s outside timing','Official LDPC 2.4.1'),('BP_OSD','AVAILABLE','D x = s outside timing','Official LDPC 2.4.1'),('Relay_BP','AVAILABLE_WITH_ELIGIBILITY_LIMITS','D x = s; retain declared nonconvergence','Official Rust release, RNG-reset commit'),('GARI','AVAILABLE_FOR_VERIFIED_MODELS','D x = s; retain nonconvergence','Official C kernel, exact augmented joint-model adapter'),('PyMatching_primary_hypergraphs','UNSUPPORTED','UNAVAILABLE','No correlation-dropping graphlike replacement')]:
        matrix.append(dict(backend=name,status=status,correction_validity=validity,provenance=source))
    atomic(ROOT/'evidence/backend_capability_matrix.json',dict(current=matrix,chronology='Initial compatibility audits are preserved; subsequent GARI transform/gates supersede initial unsupported status on verified primary models.',evidence=['gari_verified_smoke.json','gari_validation_gate.json','tesseract_optimization_ancestry.json','ldpc_header_equivalence.json','prefreeze_contract_audit.json']))
if __name__=='__main__':main()
