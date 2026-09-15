from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib, json
from typing import Any


@dataclass(frozen=True, slots=True)
class UIContract:
    operation_family: str
    family_contract_version: str
    route: str
    controls: dict[str, dict[str, Any]]
    required_args: tuple[str, ...]
    postcondition: str

    def fingerprint(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["fingerprint"] = self.fingerprint()
        return data


V1: dict[str, UIContract] = {
    "orders.lookup_status": UIContract(
        "orders.lookup_status", "v1", "/orders/status",
        {
            "order_id": {"kind": "fill", "selector": "[data-testid='order-id']"},
            "submit": {"kind": "click", "selector": "[data-testid='order-status-submit']"},
            "result": {"kind": "extract", "selector": "[data-testid='order-status-result']"},
        },
        ("order_id",), "order_status_matches_authoritative_state",
    ),
    "shipping.update_instructions": UIContract(
        "shipping.update_instructions", "v1", "/shipping/update",
        {
            "order_id": {"kind": "fill", "selector": "[data-testid='shipping-order-id']"},
            "delivery_window": {"kind": "fill", "selector": "[data-testid='delivery-window']"},
            "instructions": {"kind": "fill", "selector": "[data-testid='shipping-instructions']"},
            "submit": {"kind": "click", "selector": "[data-testid='shipping-submit']"},
        },
        ("order_id", "delivery_window", "instructions"), "shipping_instruction_persisted",
    ),
    "billing.apply_credit": UIContract(
        "billing.apply_credit", "v1", "/billing/credit",
        {
            "customer_id": {"kind": "fill", "selector": "[data-testid='billing-customer-id']"},
            "amount": {"kind": "fill", "selector": "[data-testid='billing-amount']"},
            "submit": {"kind": "click", "selector": "[data-testid='billing-submit']"},
        },
        ("customer_id", "amount"), "credit_recorded",
    ),
    "returns.create_authorization": UIContract(
        "returns.create_authorization", "v1", "/returns/create",
        {
            "order_id": {"kind": "fill", "selector": "[data-testid='return-order-id']"},
            "item_sku": {"kind": "fill", "selector": "[data-testid='return-item-sku']"},
            "reason": {"kind": "select", "selector": "[data-testid='return-reason']"},
            "submit": {"kind": "click", "selector": "[data-testid='return-submit']"},
        },
        ("order_id", "item_sku", "reason"), "rma_created",
    ),
    "customers.update_contact": UIContract(
        "customers.update_contact", "v1", "/customers/contact",
        {
            "customer_id": {"kind": "fill", "selector": "[data-testid='customer-id']"},
            "email": {"kind": "fill", "selector": "[data-testid='customer-email']"},
            "phone": {"kind": "fill", "selector": "[data-testid='customer-phone']"},
            "submit": {"kind": "click", "selector": "[data-testid='customer-submit']"},
        },
        ("customer_id", "email", "phone"), "contact_updated",
    ),
    "inventory.reserve_stock": UIContract(
        "inventory.reserve_stock", "v1", "/inventory/reserve",
        {
            "sku": {"kind": "fill", "selector": "[data-testid='inventory-sku']"},
            "location": {"kind": "fill", "selector": "[data-testid='warehouse-id']"},
            "quantity": {"kind": "fill", "selector": "[data-testid='inventory-quantity']"},
            "submit": {"kind": "click", "selector": "[data-testid='inventory-submit']"},
        },
        ("sku", "location", "quantity"), "reservation_created",
    ),
}

# V2 intentionally changes four operation families while leaving orders/customers compatible with V1.
V2: dict[str, UIContract] = {
    **{k: v for k, v in V1.items() if k in {"orders.lookup_status", "customers.update_contact"}},
    "shipping.update_instructions": UIContract(
        "shipping.update_instructions", "v2", "/shipping/details",
        {
            "order_id": {"kind": "fill", "selector": "[data-testid='shipment-order-id']"},
            "delivery_window": {"kind": "fill", "selector": "[data-testid='shipment-window']"},
            "instructions": {"kind": "fill", "selector": "[data-testid='shipment-notes']"},
            "submit": {"kind": "click", "selector": "[data-testid='shipment-save']"},
        },
        ("order_id", "delivery_window", "instructions"), "shipping_instruction_persisted",
    ),
    "billing.apply_credit": UIContract(
        "billing.apply_credit", "v2", "/billing/credit",
        {
            "customer_id": {"kind": "fill", "selector": "[data-testid='billing-customer-id']"},
            "amount": {"kind": "fill", "selector": "[data-testid='billing-amount-cents']", "transform": "dollars_to_cents"},
            "reason_code": {"kind": "select", "selector": "[data-testid='billing-reason-code']"},
            "approval_code": {"kind": "fill", "selector": "[data-testid='billing-approval-code']", "conditional": "amount_gt_100"},
            "submit": {"kind": "click", "selector": "[data-testid='billing-submit-v2']"},
        },
        ("customer_id", "amount", "reason_code"), "credit_recorded",
    ),
    "returns.create_authorization": UIContract(
        "returns.create_authorization", "v2", "/returns/create",
        {
            "order_id": {"kind": "fill", "selector": "[data-testid='return-order-id-v2']"},
            "item_sku": {"kind": "fill", "selector": "[data-testid='return-item-sku-v2']"},
            "next": {"kind": "click", "selector": "[data-testid='return-next']"},
            "reason": {"kind": "select", "selector": "[data-testid='return-reason-v2']"},
            "submit": {"kind": "click", "selector": "[data-testid='return-submit-v2']"},
        },
        ("order_id", "item_sku", "reason"), "rma_created",
    ),
    "inventory.reserve_stock": UIContract(
        "inventory.reserve_stock", "v2", "/inventory/reserve",
        {
            "sku": {"kind": "fill", "selector": "[data-testid='inventory-sku-v2']"},
            "location": {"kind": "fill", "selector": "[data-testid='location-id']"},
            "quantity": {"kind": "fill", "selector": "[data-testid='inventory-quantity-v2']"},
            "submit": {"kind": "click", "selector": "[data-testid='inventory-review']"},
            "confirm": {"kind": "click", "selector": "[data-testid='inventory-confirm']"},
        },
        ("sku", "location", "quantity"), "reservation_created",
    ),
}


def contracts_for(ui_version: str) -> dict[str, UIContract]:
    if ui_version == "V1":
        return V1
    if ui_version == "V2":
        return V2
    raise ValueError(f"Unknown UI version: {ui_version}")
