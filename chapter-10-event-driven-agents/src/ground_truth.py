from __future__ import annotations
from .models import Observation, Decision
from .contracts import get_contract

def authoritative_decision(obs: Observation) -> Decision:
    c = get_contract(obs.family, obs.contract_version)
    s = obs.state

    if obs.reasoning_required:
        # Frozen semantic labels are part of synthetic ground truth, never model inputs.
        return Decision("reasoning_action", obs.expected_label, "semantic interpretation required")

    if obs.family == "inventory_risk":
        triggered = float(s["available"]) < float(c.threshold)
    elif obs.family == "shipment_exception":
        triggered = float(s["eta_hours"]) > float(s["promised_hours"])
    elif obs.family == "order_sla":
        triggered = float(s["age_hours"]) > float(c.threshold)
    elif obs.family == "invoice_risk":
        triggered = float(s["days_overdue"]) > float(c.threshold)
    elif obs.family == "supplier_performance":
        triggered = float(s["score"]) < float(c.threshold)
    elif obs.family == "customer_account":
        triggered = float(s["risk_score"]) > float(c.threshold)
    else:
        raise ValueError(obs.family)

    return Decision("deterministic_action" if triggered else "no_action")
