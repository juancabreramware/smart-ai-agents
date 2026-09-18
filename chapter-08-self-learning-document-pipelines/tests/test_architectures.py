from pathlib import Path
import subprocess,sys,json,tempfile
ROOT=Path(__file__).resolve().parents[1]
def test_mock_demo_runs():
    subprocess.check_call([sys.executable,str(ROOT/'scripts'/'generate_corpus.py')])
    with tempfile.TemporaryDirectory(dir=ROOT) as td:
        rel=Path(td).relative_to(ROOT)
        subprocess.check_call([sys.executable,str(ROOT/'scripts'/'run_demo.py'),'--planner','mock','--output',str(rel)])
        s=json.loads((Path(td)/'execution-summary.json').read_text()); assert all(v['requests']==15 for v in s.values()); assert s['baseline']['llm_calls']==15; assert s['smart']['llm_calls']<15
