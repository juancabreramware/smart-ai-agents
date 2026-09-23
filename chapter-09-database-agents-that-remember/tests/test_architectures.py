from pathlib import Path
from src.benchmark.workload import load
from src.benchmark.runner import run
from src.planner.mock_planner import MockPlanner
ROOT=Path(__file__).resolve().parents[1]
def test_mock_benchmark(tmp_path):
    s=run(load(ROOT/'workloads'/'benchmark_v1.0.jsonl'),lambda:MockPlanner(),tmp_path,ROOT/'workloads'/'harborpoint-v1.sqlite',ROOT/'workloads'/'harborpoint-v2.sqlite')
    assert s['baseline']['requests']==150 and s['baseline']['llm_calls']==150 and s['baseline']['correct']==150
    assert s['smart']['llm_calls']==28 and s['smart']['correct']==150 and s['smart']['stale_incorrect']==0
    assert s['naive']['llm_calls']==24 and s['naive']['correct']<150 and s['naive']['stale_incorrect']>0
