from src.agents import BaselineAgent
from src.provider import MockProvider
from src.workload import build_workload, workload_hash

def test_baseline_reasons_every_time():
    w=build_workload(); h=workload_hash(w); a=BaselineAgent(MockProvider())
    rows=[a.process("test",o,h) for o in w]
    assert len(rows)==150
    assert sum(r.llm_called for r in rows)==150
    assert all(r.decision_correct for r in rows)
