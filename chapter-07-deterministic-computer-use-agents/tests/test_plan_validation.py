from smart_agents_ch7.benchmark.workload import build_benchmark
from smart_agents_ch7.planner.mock import build_plan
from smart_agents_ch7.portal.contracts import contracts_for
from smart_agents_ch7.validation.plan_validation import validate_plan


def test_mock_plans_validate_for_all_families_and_versions():
    seen = set()
    for req in build_benchmark():
        key = (req.operation_family, req.ui_version)
        if key in seen:
            continue
        seen.add(key)
        contract = contracts_for(req.ui_version)[req.operation_family]
        plan = build_plan(req, contract)
        result = validate_plan(plan, req, contract)
        assert result.ok, (key, result.reasons)
