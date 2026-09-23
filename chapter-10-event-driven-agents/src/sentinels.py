from __future__ import annotations
from .models import Sentinel, MonitorContract, Observation, Decision
from .ground_truth import authoritative_decision

class SentinelRegistry:
    def __init__(self):
        self._items: dict[str, Sentinel] = {}

    def get(self, family: str) -> Sentinel | None:
        return self._items.get(family)

    def promote(self, family: str, contract: MonitorContract) -> Sentinel:
        previous=self._items.get(family)
        version=1 if previous is None else previous.sentinel_version+1
        s=Sentinel(
            sentinel_id=f"{family}-sentinel",
            family=family,
            sentinel_version=version,
            monitor_contract_version=contract.version,
            contract_fingerprint=contract.fingerprint(),
            dependencies=contract.dependencies,
            threshold=contract.threshold,
            response_mode=contract.response_mode,
        )
        self._items[family]=s
        return s

def compatible(sentinel: Sentinel, contract: MonitorContract, obs: Observation) -> tuple[bool,str]:
    if sentinel.validation_status != "validated":
        return False,"not_validated"
    if sentinel.contract_fingerprint != contract.fingerprint():
        return False,"contract_fingerprint_changed"
    for dep in sentinel.dependencies:
        if dep not in obs.state:
            return False,f"missing_dependency:{dep}"
    return True,"compatible"

def evaluate_with_sentinel(sentinel: Sentinel, obs: Observation) -> Decision:
    # The sentinel executes known monitoring semantics without model inference.
    # It intentionally uses its stored threshold, not hidden ground truth.
    s=obs.state
    t=sentinel.threshold
    if obs.family=="inventory_risk":
        triggered=float(s["available"]) < float(t)
    elif obs.family=="shipment_exception":
        triggered=float(s["eta_hours"]) > float(s["promised_hours"])
    elif obs.family=="order_sla":
        triggered=float(s["age_hours"]) > float(t)
    elif obs.family=="invoice_risk":
        triggered=float(s["days_overdue"]) > float(t)
    elif obs.family=="supplier_performance":
        triggered=float(s["score"]) < float(t)
    elif obs.family=="customer_account":
        triggered=float(s["risk_score"]) > float(t)
    else:
        raise ValueError(obs.family)
    return Decision("deterministic_action" if triggered else "no_action")
