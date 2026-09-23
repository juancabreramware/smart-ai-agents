from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Any, Literal
import hashlib, json

Action = Literal["no_action", "deterministic_action", "reasoning_action", "relearn"]
Route = Literal["baseline_reasoning", "initial_acquisition", "deterministic_reuse", "reasoning_required", "relearning", "naive_reuse"]

@dataclass(frozen=True)
class MonitorContract:
    family: str
    version: str
    dependencies: tuple[str, ...]
    threshold: float | None
    unit: str | None
    semantic_version: str
    response_mode: str

    def fingerprint(self) -> str:
        raw = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()

@dataclass(frozen=True)
class Observation:
    observation_id: str
    sequence: int
    entity_id: str
    family: str
    contract_version: str
    timestamp: str
    state: dict[str, Any]
    previous_state: dict[str, Any]
    expected_action: Action
    expected_label: str | None = None
    reasoning_required: bool = False

@dataclass
class Sentinel:
    sentinel_id: str
    family: str
    sentinel_version: int
    monitor_contract_version: str
    contract_fingerprint: str
    dependencies: tuple[str, ...]
    threshold: float | None
    response_mode: str
    validation_status: str = "validated"

@dataclass
class ProviderUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0

@dataclass
class Decision:
    action: Action
    label: str | None = None
    explanation: str = ""

@dataclass
class EvidenceRow:
    run_id: str
    architecture: str
    observation_id: str
    sequence: int
    entity_id: str
    monitor_family: str
    monitor_contract_version: str
    route: Route
    route_reason: str
    compatibility: str
    sentinel_id: str | None
    sentinel_version: int | None
    llm_called: bool
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    measured_cost_usd: float
    model_latency_ms: float
    total_latency_ms: float
    expected_action: str
    actual_action: str
    expected_label: str | None
    actual_label: str | None
    decision_correct: bool
    false_positive: bool
    false_negative: bool
    stale_reuse: bool
    duplicate_action: bool
    workload_hash: str
    contract_fingerprint: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
