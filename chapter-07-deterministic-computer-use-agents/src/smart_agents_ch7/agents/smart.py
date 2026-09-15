from __future__ import annotations

from smart_agents_ch7.benchmark.models import BenchmarkRequest
from smart_agents_ch7.benchmark.pricing import Pricing
from smart_agents_ch7.browser.executor import BrowserExecutor
from smart_agents_ch7.browser.models import BrowserExecution
from smart_agents_ch7.capabilities.compatibility import check_compatibility
from smart_agents_ch7.capabilities.model import UICapability
from smart_agents_ch7.capabilities.registry import CapabilityRegistry
from smart_agents_ch7.planner.models import TokenUsage
from smart_agents_ch7.portal.contracts import UIContract
from smart_agents_ch7.portal.state import PortalState
from smart_agents_ch7.validation.ground_truth import audit_request
from smart_agents_ch7.validation.plan_validation import validate_plan
from .common import AgentOutcome


class SmartComputerUseAgent:
    def __init__(self, planner, executor: BrowserExecutor, state: PortalState, pricing: Pricing, registry: CapabilityRegistry | None = None):
        self.planner = planner
        self.executor = executor
        self.state = state
        self.pricing = pricing
        self.registry = registry or CapabilityRegistry()

    def _reason_execute_maybe_promote(self, request: BenchmarkRequest, contract: UIContract, route: str) -> AgentOutcome:
        planned = self.planner.plan(request, contract)
        validation = validate_plan(planned.plan, request, contract)
        promoted = False
        cap_id = None
        cap_version = None
        if validation.ok:
            execution = self.executor.execute(planned.plan, request.args)
        else:
            execution = BrowserExecution(False, error="plan_validation_failed:" + ",".join(validation.reasons))
        audit = audit_request(request, execution, self.state)
        if validation.ok and execution.ok and audit.ok and planned.plan.reusable and not request.reasoning_required:
            cap_version = self.registry.next_version(request.operation_family)
            cap_id = f"{request.operation_family.replace('.', '_')}_v{cap_version}"
            cap = UICapability(
                capability_id=cap_id,
                operation_family=request.operation_family,
                capability_version=cap_version,
                ui_contract_version=contract.family_contract_version,
                contract_fingerprint=contract.fingerprint(),
                plan=planned.plan,
                provenance={"created_by_request": request.request_id, "route": route},
            )
            self.registry.promote(cap)
            promoted = True
        return AgentOutcome(
            architecture="smart",
            request_id=request.request_id,
            routing_path=route,
            llm_called=True,
            planner_model=planned.model,
            token_usage=planned.usage,
            measured_llm_cost=self.pricing.cost(planned.usage),
            execution=execution,
            audit=audit,
            capability_id=cap_id,
            capability_version=cap_version,
            promoted=promoted,
            raw_response_id=planned.raw_response_id,
            planner_latency_ms=planned.elapsed_ms,
        )

    def handle(self, request: BenchmarkRequest, contract: UIContract) -> AgentOutcome:
        if request.reasoning_required:
            return self._reason_execute_maybe_promote(request, contract, "REASONING_REQUIRED")

        cap = self.registry.active(request.operation_family)
        if cap is None:
            return self._reason_execute_maybe_promote(request, contract, "INITIAL_ACQUISITION")

        comp = check_compatibility(cap, request, contract)
        if not comp.ok:
            self.registry.invalidate(cap, ",".join(comp.reasons))
            outcome = self._reason_execute_maybe_promote(request, contract, "RELEARNING")
            outcome.compatibility_checks = comp.to_dict()
            outcome.invalidated = True
            return outcome

        execution = self.executor.execute(cap.plan, request.args)
        audit = audit_request(request, execution, self.state)
        if execution.ok and audit.ok:
            cap.reuse_count += 1
            return AgentOutcome(
                architecture="smart",
                request_id=request.request_id,
                routing_path="DETERMINISTIC_REUSE",
                llm_called=False,
                planner_model=None,
                token_usage=TokenUsage(),
                measured_llm_cost=0.0,
                execution=execution,
                audit=audit,
                capability_id=cap.capability_id,
                capability_version=cap.capability_version,
                compatibility_checks=comp.to_dict(),
            )

        # Failure-triggered relearning: do not keep replaying the same failing capability.
        self.registry.invalidate(cap, execution.error or ";".join(audit.reasons) or "runtime_failure")
        outcome = self._reason_execute_maybe_promote(request, contract, "RELEARNING")
        outcome.compatibility_checks = comp.to_dict()
        outcome.invalidated = True
        return outcome
