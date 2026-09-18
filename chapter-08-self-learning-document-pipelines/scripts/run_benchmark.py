import argparse,json,hashlib,platform
from _common import ROOT,planner_factory
from src.benchmark.workload import load
from src.benchmark.runner import run
from src.benchmark.pricing import DEFAULT_PRICING
p=argparse.ArgumentParser(); p.add_argument('--planner',choices=['mock','openai'],default='mock'); p.add_argument('--output',required=True); a=p.parse_args(); out=ROOT/a.output; out.mkdir(parents=True,exist_ok=True)
wp=ROOT/'workloads'/'benchmark_v1.0.jsonl'
manifest={'chapter':8,'spec_version':'1.0','implementation_version':'0.1.0','planner':a.planner,'model':'mock-planner' if a.planner=='mock' else 'gpt-5.6-sol','reasoning_effort':'medium' if a.planner=='openai' else None,'pricing':DEFAULT_PRICING if a.planner=='openai' else {},'workload_sha256':hashlib.sha256(wp.read_bytes()).hexdigest(),'python':platform.python_version()}
(out/'experiment-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(run(load(wp),planner_factory(a.planner),out),indent=2))
