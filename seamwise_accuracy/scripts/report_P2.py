import sys,pathlib,json,collections
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'python'))
from common import *
from analysis import read_run,save_analysis
points=[]
for name in ['P2_current.json','P2_controls_current.json']:
 p=ROOT/json.loads((ROOT/'results'/name).read_text())['path'];save_analysis(p);points+=read_run(p)[0]
selected={};lines=['# P2 BP and stronger-solver validation','', 'New independent validation inputs, first 128 of the fixed 512-ID validation stream. These are tuning results, not confirmatory accuracy. Original and default-config copied native corrections must match exactly.','','| Workload | Point | Failures /128 | Invalid | Mean ms | p99 ms |','|---|---|---:|---:|---:|---:|']
for work in WORKS:
 ps=[p for p in points if p['workload']==work];byname={p['name']:p for p in ps};assert [r['correction_sha256'] for r in byname['original']['rows']]==[r['correction_sha256'] for r in byname['bp_reference']['rows']]
 for p in ps:lines.append(f"| {work} | {p['name']} | {p['failures']} | {p['invalid']} | {p['mean_ms']:.4g} | {p['p99_ms']:.4g} |")
 candidates=[p for p in ps if p['config'].get('kind','new')=='new' and not p['invalid']];best=min(candidates,key=lambda p:(p['failures'],p['mean_ms']));best_fast=min([p for p in candidates if p['mean_ms']<=max(2*byname['original']['mean_ms'],1.)],key=lambda p:(p['failures'],p['mean_ms']));selected[work]=dict(best=best['config'],best_fast=best_fast['config'],selection='validation only; minimum logical count then mean latency, plus a <=max(2x original mean,1ms) fast candidate',best_failures=best['failures'],best_fast_failures=best_fast['failures'])
lines+=['','Bit-serial is the official LDPC variable-serial update, not a falsely labeled check-layered implementation. The additional parallel 60-iteration control isolates iteration from schedule; the 30-iteration normalization08 control isolates scale. The damped implementation matches an independent ordered-message reference exactly on finite-LLR fixtures; official serial LLRs also match exactly. Native ASan/UBSan/leak tests exercise damped and serial syndrome/reset cases.','','No graph representation, mechanism priors or observable map was changed. Existing GARI remains a separately audited exact augmentation; unsupported/uncompleted operating points are not counted as defeated. Multi-start candidate proposals and adaptive repair are a subsequent bounded stage, justified by P0/P1 search/selection evidence and the remaining P2 validation errors.']
(ROOT/'results/P2_BP_COMPARISON.md').write_text('\n'.join(lines)+'\n');atomic(ROOT/'configs/P2_selected.json',selected);ledger('P2 exact default regression and validation report','COMPLETE',selected=selected)
