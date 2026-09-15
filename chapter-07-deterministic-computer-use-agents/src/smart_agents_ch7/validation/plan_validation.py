from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from smart_agents_ch7.benchmark.models import BenchmarkRequest
from smart_agents_ch7.browser.models import BrowserPlan
from smart_agents_ch7.portal.contracts import UIContract


@dataclass(slots=True)
class PlanValidation:
    ok: bool
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_plan(plan: BrowserPlan, request: BenchmarkRequest, contract: UIContract) -> PlanValidation:
    reasons: list[str] = []
    allowed_selectors = {
        str(meta.get("selector"))
        for meta in contract.controls.values()
        if meta.get("selector")
    }

    if plan.operation_family != request.operation_family:
        reasons.append("operation_family_mismatch")
    if plan.start_path != contract.route:
        reasons.append("route_mismatch")
    if not plan.actions or plan.actions[0].kind != "goto":
        reasons.append("plan_must_start_with_goto")
    missing_contract_args = set(contract.required_args) - set(plan.required_args)
    for arg in sorted(missing_contract_args):
        reasons.append(f"plan_omits_contract_required_arg:{arg}")
    for arg in plan.required_args:
        if arg not in request.args:
            reasons.append(f"missing_required_arg:{arg}")
    for action in plan.actions:
        if action.kind in {"fill", "select", "check", "click", "extract"}:
            if not action.target or action.target not in allowed_selectors:
                reasons.append(f"selector_not_in_contract:{action.target}")
        if action.value and action.value.startswith("{{") and action.value.endswith("}}"):
            key = action.value[2:-2].strip()
            if key not in request.args:
                reasons.append(f"placeholder_not_in_request:{key}")
    if plan.postcondition != contract.postcondition:
        reasons.append("postcondition_mismatch")
    return PlanValidation(not reasons, reasons)
