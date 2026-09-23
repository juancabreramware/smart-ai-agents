from src.agents import NaiveAgent
from src.provider import MockProvider
from src.workload import build_workload, workload_hash

def test_naive_is_unsafe_control():
    w=build_workload(); h=workload_hash(w); a=NaiveAgent(MockProvider())
    rows=[a.process("test",o,h) for o in w]
    assert sum(r.llm_called for r in rows)==24
    assert sum(r.stale_reuse for r in rows)>=1
    assert sum(not r.decision_correct for r in rows)>=1
