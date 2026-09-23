from src.contracts import V1,V2
from src.sentinels import SentinelRegistry,compatible
from src.workload import build_workload

def test_drift_invalidates_only_changed_contracts():
    reg=SentinelRegistry()
    for family,c in V1.items(): reg.promote(family,c)
    changed={f for f in V1 if V1[f].fingerprint()!=V2[f].fingerprint()}
    assert changed=={"inventory_risk","order_sla","invoice_risk","supplier_performance"}
    sample={o.family:o for o in build_workload() if o.contract_version=="V2"}
    for f in V1:
        obs=sample.get(f)
        if obs:
            ok,_=compatible(reg.get(f),V2[f],obs)
            assert ok == (f not in changed)
