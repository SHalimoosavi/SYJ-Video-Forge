from __future__ import annotations
import argparse, importlib.util, json, sys, threading
from pathlib import Path
from .engines import ENGINE_IDS
from .engines.base import EngineError
from .runtime import run_job, smoke_test
from .schema import BundleError, load_job

def main(argv=None):
    parser=argparse.ArgumentParser(prog="python -m worker",description="SYJ Video Forge GPU worker (file bundles; no inbound network)")
    sub=parser.add_subparsers(dest="command",required=True)
    run=sub.add_parser("run",help="run a validated job bundle")
    run.add_argument("job_json"); run.add_argument("--out",required=True); run.add_argument("--engine",choices=ENGINE_IDS); run.add_argument("--resume",action="store_true")
    smoke=sub.add_parser("smoke-test",help="load an AI engine and generate one short clip")
    smoke.add_argument("--engine",choices=ENGINE_IDS,default="ltx-video"); smoke.add_argument("--out",default="worker-output")
    sub.add_parser("engines",help="list documented AI engines and dependency availability")
    args=parser.parse_args(argv)
    try:
        if args.command=="engines":
            for engine_id in ENGINE_IDS:
                available=all(importlib.util.find_spec(x) is not None for x in ("torch","diffusers","transformers","accelerate"))
                print(json.dumps({"id":engine_id,"available_dependencies":available,"torch_imported":False,"note":"GPU availability is checked only when load() runs; availability does not imply hardware compatibility."}))
            return 0
        if args.command=="run":
            job=load_job(args.job_json); print(f"Validated job {job['jobId']} with {len(job['scenes'])} editable scene prompts.",flush=True)
            def progress(index,total,state): print(f"scene {index}/{total}: {state}",flush=True)
            manifest=run_job(args.job_json,args.out,args.engine,args.resume,progress_cb=progress)
            print(json.dumps({"status":manifest.get("status"),"kind":manifest.get("kind"),"result":str(Path(args.out)/"result.mp4"),"manifest":str(Path(args.out)/"manifest.json")},indent=2))
            return 0
        report=smoke_test(args.engine,args.out)
        print(json.dumps(report,indent=2))
        return 0 if report.get("status")=="passed" else 1
    except (BundleError,EngineError,ValueError,OSError) as exc:
        print(f"ERROR: {exc}",file=sys.stderr); return 1

if __name__=="__main__": raise SystemExit(main())
