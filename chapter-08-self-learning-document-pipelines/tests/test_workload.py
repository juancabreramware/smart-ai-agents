from pathlib import Path
import json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
def ensure():
    if not (ROOT/'workloads'/'benchmark_v1.0.jsonl').exists(): subprocess.check_call([sys.executable,str(ROOT/'scripts'/'generate_corpus.py')])
def test_workload_shape():
    ensure(); xs=[json.loads(x) for x in (ROOT/'workloads'/'benchmark_v1.0.jsonl').read_text().splitlines()]; assert len(xs)==150; assert sum(x['reasoning_required'] for x in xs)==18; assert sum(x['phase']=='A' for x in xs)==60; assert sum(x['phase']=='B' for x in xs)==30; assert sum(x['phase']=='C' for x in xs)==60
def test_v2_shape():
    ensure(); xs=[json.loads(x) for x in (ROOT/'workloads'/'benchmark_v1.0.jsonl').read_text().splitlines()]; c=[x for x in xs if x['phase']=='C']; assert sum(x['affected_by_drift'] for x in c)==32; assert sum(not x['affected_by_drift'] for x in c)==28
