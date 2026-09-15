from __future__ import annotations

from smart_agents_ch7.benchmark.models import BenchmarkRequest
from smart_agents_ch7.benchmark.pricing import Pricing
from smart_agents_ch7.browser.executor import BrowserExecutor
from smart_agents_ch7.planner.models import TokenUsage
from smart_agents_ch7.portal.contracts import UIContract
from smart_agents_ch7.portal.state import PortalState
from smart_agents_ch7.validation.ground_truth import audit_request
from smart_agents_ch7.validation.plan_validation import validate_plan
from .common import AgentOutcome


class BaselineComputerUseAgent:
    def __init__(self, planner, executor: BrowserExecutor, state: PortalState, pricing: Pricing):
        self.planner = planner
        self.executor = executor
        self.state = state
        self.pricing = pricing

    def handle(self, request: BenchmarkRequest, contract: UIContract) -> AgentOutcome:
        planned = self.planner.plan(request, contract)
        validation = validate_plan(planned.plan, request, contract)
        if not validation.ok:
            from smart_agents_ch7.browser.models import BrowserExecution
            execution = BrowserExecution(False, error="plan_validation_failed:" + ",".join(validation.reasons))
        else:
            execution = self.executor.execute(planned.plan, request.args)
        audit = audit_request(request, execution, self.state)
        return AgentOutcome(
            architecture="baseline",
            request_id=request.request_id,
            routing_path="REASONING",
            llm_called=True,
            planner_model=planned.model,
            token_usage=planned.usage,
            measured_llm_cost=self.pricing.cost(planned.usage),
            execution=execution,
            audit=audit,
            raw_response_id=planned.raw_response_id,
            planner_latency_ms=planned.elapsed_ms,
        )
