import argparse
import json
import pathlib
import sys
import yaml
from .common import ROOT,atomic,digest,unique_run

def read_config(path):return yaml.safe_load(pathlib.Path(path).read_text())

def main():
    parser=argparse.ArgumentParser(prog="seamwise-bench")
    sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("doctor")
    for cmd in ["prepare","test-fidelity","validate","freeze"]:
        p=sub.add_parser(cmd);p.add_argument("--config",required=True);p.add_argument("--manifest")
    p=sub.add_parser("run");p.add_argument("--manifest",required=True);p.add_argument("--config");p.add_argument("--split",choices=["validation","timing","test"]);p.add_argument("--mode",choices=["timing","accuracy","memory","diagnostics"],required=True)
    p=sub.add_parser("analyze");p.add_argument("--run",required=True)
    args=parser.parse_args()
    if args.command=="doctor":
        from .audit import environment
        v=environment();atomic(ROOT/"evidence"/"doctor.json",v);print(json.dumps(v,indent=2));return
    if args.command=="prepare":
        from .datasets import prepare
        prepare(read_config(args.config));return
    if args.command=="test-fidelity":
        from .fidelity import run_fidelity
        run_fidelity(read_config(args.config).get("count",8));return
    if args.command in ["run","validate"]:
        from .runner import run
        if not args.manifest:raise ValueError("--manifest required for validation")
        if args.config:config=read_config(args.config)
        else:
            frozen=json.loads(pathlib.Path(args.manifest).read_text())
            if frozen.get("kind")!="frozen_campaign":raise ValueError("--config required unless using a frozen campaign manifest")
            config=frozen["config"]
        mode="validation" if args.command=="validate" else args.mode
        print(run(args.manifest,config,mode,split="validation" if mode=="validation" else args.split));return
    if args.command=="freeze":
        from .datasets import verify_manifest
        from .fidelity import source_hashes
        from .runner import check_gate
        check_gate();config=read_config(args.config)
        if not args.manifest:raise ValueError("--manifest required")
        manifest=verify_manifest(args.manifest)
        if "selection_record" not in config:raise ValueError("validation-only selection_record required")
        selection=json.loads((ROOT/config["selection_record"]).read_text())
        out=unique_run("frozen-campaign")
        atomic(out/"manifest.json",dict(kind="frozen_campaign",dataset_manifest=str(pathlib.Path(args.manifest).resolve().relative_to(ROOT)),dataset_hash=digest(manifest),
               config=config,selection=selection,sources=source_hashes(),fixed_N=config.get("count",10000),N_max=10000,
               noninferiority_margin=.10,selection_scope="validation only",status="FROZEN_NOT_RUN"))
        print(out/"manifest.json");return
    if args.command=="analyze":
        from .analysis import analyze
        path=pathlib.Path(args.run)
        if not path.exists():path=ROOT/"results"/args.run
        r=analyze(path);print(json.dumps([{k:v for k,v in s.items() if k not in ["sample_ids","config"]} for s in r["summary"]],indent=2))

if __name__=="__main__":main()
