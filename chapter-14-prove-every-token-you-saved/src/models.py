from dataclasses import dataclass, asdict
from typing import Any, Optional

@dataclass(frozen=True)
class Request:
    request_id: str
    seq: int
    wave: int
    family: str
    contract_version: str
    payload: dict[str, Any]
    reasoning_required: bool = False
    failure_mode: Optional[str] = None
    pricing_epoch: str = "P1"

@dataclass
class Usage:
    input_tokens: int
    output_tokens: int
    @property
    def total_tokens(self): return self.input_tokens + self.output_tokens

@dataclass
class ProviderAttempt:
    attempt_id: str
    request_id: str
    architecture: str
    attempt_no: int
    model: str
    pricing_epoch: str
    status: str
    input_tokens: int
    output_tokens: int
    provider_cost_micro: int
    answer: Optional[bool] = None
    operation: Optional[str] = None

@dataclass
class Capability:
    capability_id: str
    family: str
    operation: str
    contract_version: str
    validated: bool
    acquired_seq: int
    reuse_count: int = 0
    invalidated_seq: Optional[int] = None
    invalidation_reason: Optional[str] = None

def record(x): return asdict(x)
