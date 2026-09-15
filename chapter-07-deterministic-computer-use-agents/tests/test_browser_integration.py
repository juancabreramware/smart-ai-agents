import os
import pytest
from smart_agents_ch7.benchmark.workload import build_benchmark
from smart_agents_ch7.browser.executor import BrowserExecutor
from smart_agents_ch7.planner.mock import build_plan
from smart_agents_ch7.portal.contracts import contracts_for
from smart_agents_ch7.portal.server import PortalHarness
from smart_agents_ch7.portal.state import PortalState
from smart_agents_ch7.validation.ground_truth import audit_request


@pytest.mark.skipif(os.getenv("CH7_RUN_PLAYWRIGHT_TESTS") != "1", reason="Set CH7_RUN_PLAYWRIGHT_TESTS=1 where Chromium localhost access is permitted")
def test_browser_executes_one_request_per_family_per_version():
    rows = build_benchmark()
    state = PortalState()
    with PortalHarness(state) as portal, BrowserExecutor(portal.base_url) as browser:
        for version in ("V1", "V2"):
            state.ui_version = version
            seen = set()
            for req in rows:
                if req.ui_version != version or req.operation_family in seen:
                    continue
                seen.add(req.operation_family)
                contract = contracts_for(version)[req.operation_family]
                plan = build_plan(req, contract)
                execution = browser.execute(plan, req.args)
                audit = audit_request(req, execution, state)
                assert execution.ok, (version, req.operation_family, execution.error)
                assert audit.ok, (version, req.operation_family, audit.reasons)
            assert len(seen) == 6
