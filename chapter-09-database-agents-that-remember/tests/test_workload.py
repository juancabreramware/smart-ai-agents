from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def rows(n): return [json.loads(x) for x in (ROOT/'workloads'/n).read_text().splitlines() if x.strip()]
def test_workload_shape():
    r=rows('benchmark_v1.0.jsonl'); assert len(r)==150; assert sum(x['reasoning_required'] for x in r)==18; assert sum(x['affected_by_drift'] for x in r)==32
def test_demo_shape(): assert len(rows('demo_v1.0.jsonl'))==15
