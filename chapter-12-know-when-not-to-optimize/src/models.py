from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Literal

DecisionKind = Literal["PROMOTE","DEFER","REASON_ONLY"]

@dataclass(frozen=True)
class Request:
    request_id: str
    sequence: int
    family: str
    version: int
    payload: dict[str, Any]
    reusable: bool = True

    def public_dict(self) -> dict[str, Any]:
        # Deliberately excludes all future schedule/drift metadata.
        return asdict(self)

@dataclass(frozen=True)
class Answer:
    action: str
    value: bool | int | float | str

@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    provider_cost_micro: int = 0

@dataclass
class OptimizationCase:
    family: str
    observed_count: int = 0
    eligible_reuse_count: int = 0
    reasoning_cost_total_micro: int = 0
    reasoning_cost_estimate_micro: int = 0
    drift_events_observed: int = 0
    validation_cost_estimate_micro: int = 0
    maintenance_cost_estimate_micro: int = 0
    future_reuse_estimate: int = 0
    safe_probability_ppm: int = 1_000_000
    expected_reuse_value_micro: int = 0
    expected_optimization_cost_micro: int = 0
    decision: str = "DEFER"
    decision_reason: str = "INSUFFICIENT_EVIDENCE"
