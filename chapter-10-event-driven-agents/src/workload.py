from __future__ import annotations
import hashlib, json, random
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from .models import Observation
from .ground_truth import authoritative_decision

FAMILIES = (
    "inventory_risk", "shipment_exception", "order_sla",
    "invoice_risk", "supplier_performance", "customer_account",
)
REASONING_LABELS = ("weather", "customs", "damage", "policy_exception")

def _state(family: str, i: int, rng: random.Random) -> dict:
    if family == "inventory_risk":
        return {"available": 25 + (i % 7)}
    if family == "shipment_exception":
        return {"eta_hours": 20 + (i % 4), "promised_hours": 24, "note": ""}
    if family == "order_sla":
        return {"age_hours": 20 + (i % 10)}
    if family == "invoice_risk":
        return {"days_overdue": i % 4, "note": ""}
    if family == "supplier_performance":
        return {"score": 90 - (i % 5)}
    return {"risk_score": 40 + (i % 8), "note": ""}

def build_workload(count: int = 150, seed: int = 1010) -> list[Observation]:
    if count != 150:
        raise ValueError("Canonical workload is exactly 150 observations.")
    rng = random.Random(seed)
    start = datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)
    observations: list[Observation] = []

    # First six observations acquire one sentinel per family.
    for i, family in enumerate(FAMILIES):
        state = _state(family, i, rng)
        obs = Observation(
            observation_id=f"obs-{i+1:03d}", sequence=i+1, entity_id=f"{family[:3]}-001",
            family=family, contract_version="V1", timestamp=(start+timedelta(minutes=i)).isoformat(),
            state=state, previous_state=state.copy(), expected_action="no_action",
        )
        d = authoritative_decision(obs)
        observations.append(replace(obs, expected_action=d.action, expected_label=d.label))

    # Remaining rows start as deterministic/no-op observations.
    for i in range(6, count):
        family = FAMILIES[i % len(FAMILIES)]
        version = "V1" if i < 90 else "V2"
        state = _state(family, i, rng)
        prev = _state(family, i-1, rng)
        obs = Observation(
            observation_id=f"obs-{i+1:03d}", sequence=i+1, entity_id=f"{family[:3]}-{(i%5)+1:03d}",
            family=family, contract_version=version, timestamp=(start+timedelta(minutes=i)).isoformat(),
            state=state, previous_state=prev, expected_action="no_action",
        )
        d = authoritative_decision(obs)
        observations.append(replace(obs, expected_action=d.action, expected_label=d.label))

    # Exactly 18 frozen reasoning-required events after initial acquisition.
    reasoning_idx = [12,18,24,30,36,42,48,54,60,66,72,78,96,102,108,114,120,126]
    for n, idx in enumerate(reasoning_idx):
        o = observations[idx]
        label = REASONING_LABELS[n % len(REASONING_LABELS)]
        state = dict(o.state)
        state["note"] = f"synthetic operational note {n+1}"
        observations[idx] = replace(o, state=state, reasoning_required=True,
                                    expected_action="reasoning_action", expected_label=label)

    # Make four post-drift observations semantically different under V2 but executable under stale V1.
    drift_rows = {
        90: ("inventory_risk", {"available": 17.0}),       # V1 no-action, V2 trigger
        92: ("order_sla", {"age_hours": 40.0}),           # V1 no-action, V2 trigger
        94: ("invoice_risk", {"days_overdue": 6.0, "note": ""}), # V1 no-action, V2 trigger
        98: ("supplier_performance", {"score": 82.0}),     # V1 no-action, V2 trigger
    }
    for idx,(family,state) in drift_rows.items():
        o=observations[idx]
        o=replace(o, family=family, contract_version="V2", state=state, reasoning_required=False,
                  expected_label=None)
        d=authoritative_decision(o)
        observations[idx]=replace(o, expected_action=d.action)

    return observations

def workload_hash(observations: list[Observation]) -> str:
    raw=json.dumps([asdict(x) for x in observations],sort_keys=True,separators=(",",":"))
    return hashlib.sha256(raw.encode()).hexdigest()

def demo_workload() -> list[Observation]:
    full=build_workload()
    # Includes acquisition, deterministic reuse, reasoning, and all four drift rows.
    idx=[0,1,2,3,4,5,12,18,25,50,90,92,94,98,120]
    return [full[i] for i in idx]
