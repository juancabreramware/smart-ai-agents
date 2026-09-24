from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

@dataclass(frozen=True)
class Request:
    request_id: str
    sequence: int
    wave: int
    family: str
    version: str
    payload: dict[str, Any]
    reasoning_required: bool = False

@dataclass(frozen=True)
class Answer:
    value: Any

@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

@dataclass(frozen=True)
class ProviderResult:
    answer: Answer
    operation: str
    usage: Usage

@dataclass
class ValidatedCapability:
    capability_id: str
    family: str
    operation: str
    contract_version: str
    input_schema: str
    output_schema: str
    implementation_hash: str
    dependency_fingerprint: str
    policy_fingerprint: str
    environment_fingerprint: str
    validation_suite_id: str
    validation_status: str
    provenance: dict[str, Any]
    acquired_at_sequence: int
    last_validated_sequence: int
    reuse_count: int = 0
    invalidation_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
