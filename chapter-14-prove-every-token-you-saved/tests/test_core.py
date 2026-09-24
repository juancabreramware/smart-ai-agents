from src.workload import build_workload, workload_hash
from src.scoring import truth
from src.contracts import public_contract,ALLOWLIST
from src.accounting import provider_cost_micro
def test_workload_240_unique():
    w=build_workload(); assert len(w)==240; assert len({x.request_id for x in w})==240
def test_four_waves():
    w=build_workload(); assert [sum(x.wave==i for x in w) for i in range(1,5)]==[60,60,60,60]
def test_drift_versions():
    w=build_workload(); assert any(x.wave==3 and x.family=="invoice" and x.contract_version=="v2" for x in w)
def test_allowlist_closed():
    assert "invoice_escalate" in ALLOWLIST and len(ALLOWLIST)==8
def test_pricing_integer():
    assert isinstance(provider_cost_micro("gpt-5-mini","P1",1000,500),int)
def test_truth_boolean():
    assert all(isinstance(truth(x),bool) for x in build_workload(30))
def test_workload_hash_stable():
    assert workload_hash(build_workload())==workload_hash(build_workload())
