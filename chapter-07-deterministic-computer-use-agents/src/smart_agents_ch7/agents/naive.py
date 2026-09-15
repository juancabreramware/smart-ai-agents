from __future__ import annotations

from smart_agents_ch7.benchmark.models import BenchmarkRequest
from smart_agents_ch7.benchmark.pricing import Pricing
from smart_agents_ch7.browser.executor import BrowserExecutor
from smart_agents_ch7.browser.models import BrowserExecution, BrowserPlan
from smart_agents_ch7.planner.models import TokenUsage
from smart_agents_ch7.portal.contracts import UIContract
from smart_agents_ch7.portal.state import PortalState
from smart_agents_ch7.validation.ground_truth import audit_request
from smart_agents_ch7.validation.plan_validation import validate_plan
from .common import AgentOutcome


class NaiveReplayAgent:
    """Aggressive procedure reuse without UI-contract compatibility validation.

    To isolate the stale-replay defect, explicit reasoning-required requests still call the planner.
    What Naive omits is Smart's compatibility, selective invalidation, and versioned relearning path.
    """

    def __init__(self, planner, executor: BrowserExecutor, state: PortalState, pricing: Pricing):
        self.planner = planner
        self.executor = executor
        self.state = state
        self.pricing = pricing
        self.cache: dict[str, BrowserPlan] = {}

    def _reason(self, request: BenchmarkRequest, contract: UIContract, cache: bool) -> AgentOutcome:
        planned = self.planner.plan(request, contract)
        validation = validate_plan(planned.plan, request, contract)
        if validation.ok:
            execution = self.executor.execute(planned.plan, request.args)
        else:
            execution = BrowserExecution(False, error="plan_validation_failed:" + ",".join(validation.reasons))
        audit = audit_request(request, execution, self.state)
        if cache and validation.ok and execution.ok and audit.ok:
            self.cache[request.operation_family] = planned.plan
        return AgentOutcome(
            architecture="naive",
            request_id=request.request_id,
            routing_path="REASONING_REQUIRED" if request.reasoning_required else "INITIAL_ACQUISITION",
            llm_called=True,
            planner_model=planned.model,
            token_usage=planned.usage,
            measured_llm_cost=self.pricing.cost(planned.usage),
            execution=execution,
            audit=audit,
            raw_response_id=planned.raw_response_id,
            planner_latency_ms=planned.elapsed_ms,
        )

    def handle(self, request: BenchmarkRequest, contract: UIContract) -> AgentOutcome:
        if request.reasoning_required:
            return self._reason(request, contract, cache=False)
        if request.operation_family not in self.cache:
            return self._reason(request, contract, cache=True)

        # Intentionally no contract/version/fingerprint check here.
        plan = self.cache[request.operation_family]
        execution = self.executor.execute(plan, request.args)
        audit = audit_request(request, execution, self.state)
        stale = request.v2_affected and request.ui_version == "V2" and not audit.ok
        return AgentOutcome(
            architecture="naive",
            request_id=request.request_id,
            routing_path="NAIVE_REUSE",
            llm_called=False,
            planner_model=None,
            token_usage=TokenUsage(),
            measured_llm_cost=0.0,
            execution=execution,
            audit=audit,
            stale_reuse=stale,
        )
