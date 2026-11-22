#!/usr/bin/env python3
"""Freeze full-repair policies and a budgeted campaign from validation only."""
import json,pathlib,sys
import yaml
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from seamwise_bench.common import ROOT,atomic,sha

FAMILIES=['tesseract','lsd','osd','relay','gari']
def normalized(cfg):
    c={k:v for k,v in cfg.items() if k!='name'}
    if c['kind']=='native':
        for k,v in dict(iterations=30,order=0,persistent=True,dense_terminal=False).items():c.setdefault(k,v)
    return c

def main(path):
    path=pathlib.Path(path).resolve();ledger=json.loads((path/'execution_ledger.json').read_text());trials=[];selected={}
    for original in ledger:
        j=dict(original);jobfile=path/j['job_id']/'job.json'
        if jobfile.exists():
            source=json.loads(jobfile.read_text())
            j.setdefault('workload',source['workload']);j.setdefault('backend',source['backend']['name']);j.setdefault('backend_config',source['backend'])
        j['eligible_for_selection']=j['status']=='COMPLETE' and j.get('invalid',1)==0
        if j['eligible_for_selection']:
            if j['split']!='validation':raise ValueError('Tuning requires validation data')
            rows=[json.loads(line) for line in (path/j['job_id']/'shots.jsonl').read_text().splitlines()]
            j['logical_failures']=sum(r['logical_failure'] for r in rows)
        trials.append(j)
    best=lambda js:min(js,key=lambda j:(j['logical_failures'],j['latency_ns']['mean']))
    for work in sorted({j['workload'] for j in trials}):
        jobs=[j for j in trials if j['workload']==work and j['eligible_for_selection']]
        extern=[j for j in jobs if j['backend_config']['kind']!='native']
        if not extern:raise RuntimeError('No fully validated external reference: '+work)
        reference=best(extern);threshold=1.10*reference['logical_failures'];families={}
        for family in FAMILIES:
            candidates=[j for j in extern if j['backend_config']['kind']==family]
            eligible=[j for j in candidates if j['logical_failures']<=threshold]
            chosen=min(eligible,key=lambda j:j['latency_ns']['mean']) if eligible else best(candidates) if candidates else None
            families[family]=None if chosen is None else dict(config=chosen['backend_config'],validation_failures=chosen['logical_failures'],validation_point_qualified=bool(eligible),mean_ns=chosen['latency_ns']['mean'])
        # Full Seamwise must retain repair. Halo-only initialization remains an
        # ablation and cannot silently become the full-method candidate.
        full=[j for j in jobs if j['backend_config']['kind']=='native' and j['backend_config'].get('policy','').startswith('repair')]
        if not full:raise RuntimeError('No validated full repair candidate: '+work)
        qualified=[j for j in full if j['logical_failures']<=threshold]
        candidate=min(qualified,key=lambda j:j['latency_ns']['mean']) if qualified else best(full)
        selected[work]=dict(reference_backend=reference['backend_config'],reference_validation_failures=reference['logical_failures'],validation_n=reference['requested'],quality_target=reference['logical_failures']/reference['requested'],margin=.10,
                            candidate=candidate['backend_config'],candidate_validation_failures=candidate['logical_failures'],candidate_meets_validation_point_target=bool(qualified),candidate_mean_ns=candidate['latency_ns']['mean'],reference_mean_ns=reference['latency_ns']['mean'],baselines=families,
                            planning_N=10000,planning_expected_reference_failures=10000*reference['logical_failures']/reference['requested'])
    templates={family:next((j['backend_config'] for j in trials if j['backend_config']['kind']==family),None) for family in FAMILIES}
    backends=[dict(name='native_rebuild',kind='native',family='bphuf',policy='repair1',persistent=False),dict(name='native_persistent',kind='native',family='bphuf',policy='repair1',persistent=True),dict(next(iter(selected.values()))['candidate'],name='seamwise_selected')]
    for family in FAMILIES:backends.append(dict(templates[family],name='tuned_'+family))
    config=dict(workloads=list(selected),count=10000,repetitions=7,warmup=16,budgets=dict(preparation=120,decode=10800,memory=180),stage_wall_budgets=dict(timing=1800,accuracy=10800,memory=900),campaign_wall_budget_s=4*3600,
                selection_record='evidence/selection_record.json',backends=backends,workload_backend_overrides={},deferred_jobs={},quality_reference_labels={})
    forecasts={}
    for work,r in selected.items():
        overrides={'seamwise_selected':dict(r['candidate'],name='seamwise_selected')};deferred={}
        for family,point in r['baselines'].items():
            name='tuned_'+family
            if point:overrides[name]=dict(point['config'],name=name)
            reason='Secondary baseline retained with all validation evidence; fixed-N confirmatory CPU budget reserved for the strongest observed completed external reference and full Seamwise. No inferential defeat claim about deferred families.'
            if point is None:reason='No completed zero-invalid validation point; retain nonconvergence/timeouts and missing tuning trials. Backend remains available, but correction eligibility is not established.'
            if point is None or not point['validation_point_qualified']:
                deferred[name]={m:reason for m in ['timing','accuracy','memory']}
            else:
                # Full fixed-N primary accuracy runs retain the strongest
                # completed validation-quality reference. Other families are
                # secondary unless they are that exact operating point.
                if normalized(point['config'])!=normalized(r['reference_backend']):deferred[name]={m:reason for m in ['timing','accuracy','memory']}
        family=r['reference_backend']['kind'];label='tuned_'+family
        if normalized(overrides.get(label,templates[family]))!=normalized(r['reference_backend']):
            raise RuntimeError('Reference needs a distinct operating-point label')
        config['quality_reference_labels'][work]=label
        if not r['candidate_meets_validation_point_target']:
            deferred.setdefault(label,{})['timing']='Full Seamwise failed the frozen validation point quality screen. Raw speed cannot form S_frontier; independent fixed-N accuracy is still run. This gate is declared before test observations.'
        # Native exact-policy timing remains primary on every workload, even
        # where the scientific frontier is ineligible.
        for name in ['tuned_tesseract','tuned_lsd','tuned_osd','tuned_relay','tuned_gari']:
            deferred.setdefault(name,{})['memory']='Primary full-corpus memory/soak audit is reserved for the three native Seamwise operating points; external RSS from validation/accuracy is retained, with no exact external-workspace claim.'
        config['workload_backend_overrides'][work]=overrides;config['deferred_jobs'][work]=deferred
        forecasts[work]=dict(reference_10000_cpu_hours=r['reference_mean_ns']*10000/1e9/3600,seamwise_10000_cpu_hours=r['candidate_mean_ns']*10000/1e9/3600,
                             reference_1024x7_cpu_hours=r['reference_mean_ns']*1024*7/1e9/3600,scope='validation mean-based forecast; hard-tail uncertainty can exhaust stage budget; fixed N is never shortened after outcomes')
    record=dict(status='FROZEN_FROM_VALIDATION_ONLY',validation_run=str(path.relative_to(ROOT)),validation_ledger_sha256=sha(path/'execution_ledger.json'),selected=selected,trials=trials,
                selection_rule='reference=min logical failures then latency among complete zero-invalid external trials; per family fastest at <=1.10 reference validation count, else best accuracy marked not qualified; full Seamwise restricts candidates to repair policies',
                final_test_opened=False,confirmatory_N_rule='N=min(10000,max(10000,ceil(400/max(p_validation,1e-6))))=10000; rare/capped precision stated explicitly',
                primary_aggregate='equal-workload-weight geometric mean across all three declared workloads; S_frontier aggregate ineligible if any required quality comparison is unresolved/ineligible',
                multiple_comparisons='simultaneous paired exact-cell Bonferroni bounds across all reported primary workload comparisons',compute_forecast=forecasts,
                budget_seconds=dict(accuracy=10800,timing=1800,memory=900),deferred_families_remain_unresolved=True)
    atomic(ROOT/'evidence/selection_record.json',record)
    (ROOT/'configs/final.yaml').write_text(yaml.safe_dump(config,sort_keys=False))
    print(json.dumps(dict(selected=selected,compute_forecast=forecasts),indent=2))

if __name__=='__main__':main(sys.argv[1])
