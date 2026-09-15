from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from smart_agents_ch7.benchmark.models import BenchmarkRequest
from smart_agents_ch7.browser.models import BrowserExecution
from smart_agents_ch7.portal.state import PortalState


@dataclass(slots=True)
class AuditResult:
    ok: bool
    reasons: list[str]
    observed: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def audit_request(request: BenchmarkRequest, execution: BrowserExecution, state: PortalState) -> AuditResult:
    reasons: list[str] = []
    observed: dict[str, Any] = {}

    if not execution.ok:
        reasons.append("browser_execution_failed")

    f = request.operation_family
    a = request.args

    if f == "orders.lookup_status":
        expected = state.orders.get(a["order_id"], {}).get("status")
        actual = execution.extracted.get("order_status")
        observed = {"expected": expected, "actual": actual}
        if actual != expected:
            reasons.append("order_status_mismatch")

    elif f == "shipping.update_instructions":
        actual = state.shipping.get(a["order_id"])
        expected = {"delivery_window": a["delivery_window"], "instructions": a["instructions"]}
        observed = {"expected": expected, "actual": actual}
        if actual != expected:
            reasons.append("shipping_state_mismatch")

    elif f == "billing.apply_credit":
        matches = [x for x in state.credits if x["customer_id"] == a["customer_id"] and abs(float(x["amount"]) - float(a["amount"])) < 1e-9]
        observed = {"matching_credits": matches}
        if not matches:
            reasons.append("credit_not_recorded")
        elif request.ui_version == "V2":
            latest = matches[-1]
            if latest.get("reason_code") != a.get("reason_code"):
                reasons.append("credit_reason_code_mismatch")
            if float(a["amount"]) > 100 and latest.get("approval_code") != a.get("approval_code"):
                reasons.append("credit_approval_mismatch")

    elif f == "returns.create_authorization":
        expected = {"order_id": a["order_id"], "item_sku": a["item_sku"], "reason": a["reason"]}
        observed = {"expected": expected, "returns_tail": state.returns[-3:]}
        if expected not in state.returns:
            reasons.append("rma_not_created")

    elif f == "customers.update_contact":
        actual = state.customers.get(a["customer_id"])
        expected = {"email": a["email"], "phone": a["phone"]}
        observed = {"expected": expected, "actual": actual}
        if actual != expected:
            reasons.append("contact_state_mismatch")

    elif f == "inventory.reserve_stock":
        expected = {"sku": a["sku"], "location": a["location"], "quantity": int(a["quantity"])}
        observed = {"expected": expected, "reservations_tail": state.reservations[-3:]}
        if expected not in state.reservations:
            reasons.append("reservation_not_created")

    else:
        reasons.append("unknown_operation_family")

    return AuditResult(not reasons, reasons, observed)
