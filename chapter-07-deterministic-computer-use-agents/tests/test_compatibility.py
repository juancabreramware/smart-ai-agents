from smart_agents_ch7.benchmark.workload import build_benchmark
from smart_agents_ch7.capabilities.compatibility import check_compatibility
from smart_agents_ch7.capabilities.model import UICapability
from smart_agents_ch7.planner.mock import build_plan
from smart_agents_ch7.portal.contracts import V1, V2


def test_v1_capability_rejected_after_affected_v2_change():
    req = next(r for r in build_benchmark() if r.operation_family == "billing.apply_credit")
    plan = build_plan(req, V1[req.operation_family])
    cap = UICapability("billing_v1", req.operation_family, 1, "v1", V1[req.operation_family].fingerprint(), plan)
    v2_req = next(r for r in build_benchmark() if r.ui_version == "V2" and r.operation_family == req.operation_family)
    result = check_compatibility(cap, v2_req, V2[req.operation_family])
    assert not result.ok
    assert "ui_contract_version" in result.reasons
    assert "contract_fingerprint" in result.reasons


def test_unchanged_capability_remains_compatible_in_v2():
    req = next(r for r in build_benchmark() if r.operation_family == "orders.lookup_status")
    plan = build_plan(req, V1[req.operation_family])
    cap = UICapability("orders_v1", req.operation_family, 1, "v1", V1[req.operation_family].fingerprint(), plan)
    v2_req = next(r for r in build_benchmark() if r.ui_version == "V2" and r.operation_family == req.operation_family)
    result = check_compatibility(cap, v2_req, V2[req.operation_family])
    assert result.ok
