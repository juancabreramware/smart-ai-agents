from __future__ import annotations

from smart_agents_ch7.benchmark.models import BenchmarkRequest
from smart_agents_ch7.browser.models import BrowserAction, BrowserPlan
from smart_agents_ch7.portal.contracts import UIContract
from .models import PlannerResult, TokenUsage


def _action(kind: str, selector: str | None = None, value: str | None = None, key: str | None = None) -> BrowserAction:
    return BrowserAction(kind=kind, target=selector, value=value, key=key)  # type: ignore[arg-type]


def build_plan(request: BenchmarkRequest, contract: UIContract) -> BrowserPlan:
    f = request.operation_family
    c = contract.controls
    actions: list[BrowserAction] = [_action("goto", contract.route)]

    if f == "orders.lookup_status":
        actions += [
            _action("fill", c["order_id"]["selector"], "{{order_id}}"),
            _action("click", c["submit"]["selector"]),
            _action("extract", c["result"]["selector"], key="order_status"),
        ]
    elif f == "shipping.update_instructions":
        actions += [
            _action("fill", c["order_id"]["selector"], "{{order_id}}"),
            _action("fill", c["delivery_window"]["selector"], "{{delivery_window}}"),
            _action("fill", c["instructions"]["selector"], "{{instructions}}"),
            _action("click", c["submit"]["selector"]),
        ]
    elif f == "billing.apply_credit":
        actions += [_action("fill", c["customer_id"]["selector"], "{{customer_id}}")]
        if contract.family_contract_version == "v1":
            actions += [
                _action("fill", c["amount"]["selector"], "{{amount}}"),
                _action("click", c["submit"]["selector"]),
            ]
        else:
            actions += [
                _action("fill", c["amount"]["selector"], "{{amount_cents}}"),
                _action("select", c["reason_code"]["selector"], "{{reason_code}}"),
            ]
            # Approval is present in every V2 plan. The request generator supplies it when required.
            actions += [_action("fill", c["approval_code"]["selector"], "{{approval_code}}")]
            actions += [_action("click", c["submit"]["selector"])]
    elif f == "returns.create_authorization":
        if contract.family_contract_version == "v1":
            actions += [
                _action("fill", c["order_id"]["selector"], "{{order_id}}"),
                _action("fill", c["item_sku"]["selector"], "{{item_sku}}"),
                _action("select", c["reason"]["selector"], "{{reason}}"),
                _action("click", c["submit"]["selector"]),
            ]
        else:
            actions += [
                _action("fill", c["order_id"]["selector"], "{{order_id}}"),
                _action("fill", c["item_sku"]["selector"], "{{item_sku}}"),
                _action("click", c["next"]["selector"]),
                _action("select", c["reason"]["selector"], "{{reason}}"),
                _action("click", c["submit"]["selector"]),
            ]
    elif f == "customers.update_contact":
        actions += [
            _action("fill", c["customer_id"]["selector"], "{{customer_id}}"),
            _action("fill", c["email"]["selector"], "{{email}}"),
            _action("fill", c["phone"]["selector"], "{{phone}}"),
            _action("click", c["submit"]["selector"]),
        ]
    elif f == "inventory.reserve_stock":
        actions += [
            _action("fill", c["sku"]["selector"], "{{sku}}"),
            _action("fill", c["location"]["selector"], "{{location}}"),
            _action("fill", c["quantity"]["selector"], "{{quantity}}"),
            _action("click", c["submit"]["selector"]),
        ]
        if contract.family_contract_version == "v2":
            actions += [_action("click", c["confirm"]["selector"])]
    else:
        raise ValueError(f"Unknown operation family: {f}")

    required = list(contract.required_args)
    return BrowserPlan(
        operation_family=f,
        start_path=contract.route,
        actions=actions,
        required_args=required,
        postcondition=contract.postcondition,
        reusable=not request.reasoning_required,
    )


class MockPlanner:
    model = "mock-planner-v1"

    def plan(self, request: BenchmarkRequest, contract: UIContract) -> PlannerResult:
        return PlannerResult(build_plan(request, contract), TokenUsage(), self.model)
