import argparse,json
from _common import ROOT,planner_factory
from src.benchmark.workload import load
from src.benchmark.runner import run
p=argparse.ArgumentParser(); p.add_argument('--planner',choices=['mock','openai'],default='mock'); p.add_argument('--output',required=True); a=p.parse_args(); print(json.dumps(run(load(ROOT/'workloads'/'demo_v1.0.jsonl'),planner_factory(a.planner),ROOT/a.output,ROOT/'workloads'/'harborpoint-v1.sqlite',ROOT/'workloads'/'harborpoint-v2.sqlite'),indent=2))
