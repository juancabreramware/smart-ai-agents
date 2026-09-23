from __future__ import annotations
from .models import MonitorContract

V1 = {
    "inventory_risk": MonitorContract("inventory_risk", "V1", ("available",), 20.0, "units", "inventory-policy-1", "deterministic"),
    "shipment_exception": MonitorContract("shipment_exception", "V1", ("eta_hours", "promised_hours"), 0.0, "hours", "shipment-policy-1", "mixed"),
    "order_sla": MonitorContract("order_sla", "V1", ("age_hours",), 48.0, "hours", "order-policy-1", "deterministic"),
    "invoice_risk": MonitorContract("invoice_risk", "V1", ("days_overdue",), 7.0, "days", "invoice-policy-1", "mixed"),
    "supplier_performance": MonitorContract("supplier_performance", "V1", ("score",), 80.0, "score", "supplier-policy-1", "deterministic"),
    "customer_account": MonitorContract("customer_account", "V1", ("risk_score",), 70.0, "score", "customer-policy-1", "mixed"),
}

# Four families drift in V2. Shipment and customer remain compatible.
V2 = {
    "inventory_risk": MonitorContract("inventory_risk", "V2", ("available",), 15.0, "units", "inventory-policy-2", "deterministic"),
    "shipment_exception": MonitorContract("shipment_exception", "V1", ("eta_hours", "promised_hours"), 0.0, "hours", "shipment-policy-1", "mixed"),
    "order_sla": MonitorContract("order_sla", "V2", ("age_hours",), 36.0, "hours", "order-policy-2", "deterministic"),
    "invoice_risk": MonitorContract("invoice_risk", "V2", ("days_overdue",), 5.0, "days", "invoice-policy-2", "mixed"),
    "supplier_performance": MonitorContract("supplier_performance", "V2", ("score",), 85.0, "score", "supplier-policy-2", "deterministic"),
    "customer_account": MonitorContract("customer_account", "V1", ("risk_score",), 70.0, "score", "customer-policy-1", "mixed"),
}

def get_contract(family: str, version: str) -> MonitorContract:
    table = V1 if version == "V1" else V2
    return table[family]


# Public operational semantics supplied to the real reasoning provider.
# These are derived from the same frozen MonitorContract objects used by the
# deterministic sentinels. They contain no benchmark expected answers.
_TRIGGER_RULES = {
    "inventory_risk": {
        "operator": "<",
        "left": "state.available",
        "right": "contract.threshold",
        "meaning": "Trigger when available inventory is below the frozen threshold.",
    },
    "shipment_exception": {
        "operator": ">",
        "left": "state.eta_hours",
        "right": "state.promised_hours",
        "meaning": "Trigger when ETA hours exceed promised hours.",
    },
    "order_sla": {
        "operator": ">",
        "left": "state.age_hours",
        "right": "contract.threshold",
        "meaning": "Trigger when order age exceeds the frozen SLA threshold.",
    },
    "invoice_risk": {
        "operator": ">",
        "left": "state.days_overdue",
        "right": "contract.threshold",
        "meaning": "Trigger when days overdue exceed the frozen threshold.",
    },
    "supplier_performance": {
        "operator": "<",
        "left": "state.score",
        "right": "contract.threshold",
        "meaning": "Trigger when supplier score is below the frozen threshold.",
    },
    "customer_account": {
        "operator": ">",
        "left": "state.risk_score",
        "right": "contract.threshold",
        "meaning": "Trigger when customer risk score exceeds the frozen threshold.",
    },
}

def public_contract(family: str, version: str) -> dict:
    """Return the non-hidden monitoring contract visible to an operational agent."""
    c = get_contract(family, version)
    rule = _TRIGGER_RULES[family]
    return {
        "family": c.family,
        "requested_contract_version": version,
        "effective_contract_version": c.version,
        "semantic_version": c.semantic_version,
        "dependencies": list(c.dependencies),
        "threshold": c.threshold,
        "unit": c.unit,
        "response_mode": c.response_mode,
        "trigger_predicate": dict(rule),
        "action_semantics": {
            "predicate_false": "no_action",
            "predicate_true": "deterministic_action",
            "semantic_interpretation_required": "reasoning_action",
        },
    }
