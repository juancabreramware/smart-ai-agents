from __future__ import annotations

import time
from typing import Any

from smart_agents_ch7.portal.contracts import contracts_for
from smart_agents_ch7.portal.state import PortalState
from .models import BrowserExecution, BrowserPlan


class SimulatedBrowserExecutor:
    """Deterministic in-process executor used for fast local architecture validation.

    It enforces the active UI contract (route + selectors) and mutates the same authoritative
    HarborPoint business state as the browser portal. It is intentionally not the canonical
    computer-use benchmark executor; canonical real evidence should use Playwright.
    """

    def __init__(self, state: PortalState):
        self.state = state

    def __enter__(self) -> "SimulatedBrowserExecutor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, plan: BrowserPlan, args: dict[str, Any]) -> BrowserExecution:
        started = time.perf_counter()
        contract = contracts_for(self.state.ui_version)[plan.operation_family]
        allowed = {
            str(meta.get("selector"))
            for meta in contract.controls.values()
            if meta.get("selector")
        }
        if plan.start_path != contract.route:
            return BrowserExecution(False, error=f"stale_route:{plan.start_path}!={contract.route}", elapsed_ms=(time.perf_counter()-started)*1000)
        for action in plan.actions:
            if action.kind in {"fill", "select", "check", "click", "extract"} and action.target not in allowed:
                return BrowserExecution(False, error=f"stale_selector:{action.target}", elapsed_ms=(time.perf_counter()-started)*1000)

        f = plan.operation_family
        extracted: dict[str, str] = {}
        if f == "orders.lookup_status":
            status = self.state.orders.get(args["order_id"], {}).get("status")
            if status is None:
                return BrowserExecution(False, error="unknown_order", elapsed_ms=(time.perf_counter()-started)*1000)
            extracted["order_status"] = str(status)
        elif f == "shipping.update_instructions":
            self.state.shipping[args["order_id"]] = {
                "delivery_window": args["delivery_window"],
                "instructions": args["instructions"],
            }
        elif f == "billing.apply_credit":
            if args["customer_id"] not in self.state.customers:
                return BrowserExecution(False, error="unknown_customer", elapsed_ms=(time.perf_counter()-started)*1000)
            rec = {
                "customer_id": args["customer_id"],
                "amount": round(float(args["amount"]), 2),
                "reason_code": args.get("reason_code") if self.state.ui_version == "V2" else None,
                "approval_code": args.get("approval_code") if self.state.ui_version == "V2" else None,
            }
            if self.state.ui_version == "V2" and float(args["amount"]) > 100 and not rec["approval_code"]:
                return BrowserExecution(False, error="approval_required", elapsed_ms=(time.perf_counter()-started)*1000)
            self.state.credits.append(rec)
        elif f == "returns.create_authorization":
            self.state.returns.append({
                "order_id": args["order_id"],
                "item_sku": args["item_sku"],
                "reason": args["reason"],
            })
        elif f == "customers.update_contact":
            self.state.customers[args["customer_id"]] = {"email": args["email"], "phone": args["phone"]}
        elif f == "inventory.reserve_stock":
            self.state.reservations.append({
                "sku": args["sku"],
                "location": args["location"],
                "quantity": int(args["quantity"]),
            })
        else:
            return BrowserExecution(False, error=f"unknown_family:{f}", elapsed_ms=(time.perf_counter()-started)*1000)

        return BrowserExecution(True, extracted=extracted, action_count=len(plan.actions), elapsed_ms=(time.perf_counter()-started)*1000)
