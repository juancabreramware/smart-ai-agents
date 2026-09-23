from src.agents import SmartAgent
from src.provider import MockProvider
from src.workload import build_workload, workload_hash

def test_smart_has_expected_designed_routes():
    w=build_workload(); h=workload_hash(w); a=SmartAgent(MockProvider())
    rows=[a.process("test",o,h) for o in w]
    routes={}
    for r in rows: routes[r.route]=routes.get(r.route,0)+1
    assert routes["initial_acquisition"]==6
    assert routes["reasoning_required"]==18
    assert routes["relearning"]==4
    assert routes["deterministic_reuse"]==122
    assert sum(r.llm_called for r in rows)==28
    assert all(not r.llm_called for r in rows if r.route=="deterministic_reuse")
    assert all(r.decision_correct for r in rows)
