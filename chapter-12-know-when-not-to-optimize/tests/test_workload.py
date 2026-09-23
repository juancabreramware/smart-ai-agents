from src.workload import build,workload_hash
from src.contracts import FAMILIES
def test_180_and_30_each():
    w=build(); assert len(w)==180
    assert {f:sum(r.family==f for r in w) for f in FAMILIES}=={f:30 for f in FAMILIES}
def test_hash_deterministic(): assert workload_hash(build())==workload_hash(build())
def test_no_future_metadata():
    forbidden={"future_count","next_drift","remaining_family_count","true_lifetime"}
    assert all(not(forbidden & set(r.public_dict())) for r in build())
