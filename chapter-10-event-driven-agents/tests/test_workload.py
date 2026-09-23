from src.workload import build_workload, workload_hash
def test_canonical_workload_is_frozen_shape():
    w=build_workload()
    assert len(w)==150
    assert len({x.observation_id for x in w})==150
    assert sum(x.reasoning_required for x in w)==18
    assert workload_hash(w)==workload_hash(build_workload())
