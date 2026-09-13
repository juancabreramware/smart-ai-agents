from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any
import hashlib, json

@dataclass
class ApiStep:
    api: str
    operation: str
    parameter_map: list[dict[str, str]] = field(default_factory=list)
    constants: dict[str, Any] = field(default_factory=dict)
    auth_scope: str = ''

    def to_dict(self): return asdict(self)
    @staticmethod
    def from_dict(d): return ApiStep(**d)

@dataclass
class IntegrationPlan:
    operation_family: str
    steps: list[ApiStep]
    contract_version: int
    reusable: bool = True

    def to_dict(self):
        return {"operation_family": self.operation_family, "steps": [s.to_dict() for s in self.steps],
                "contract_version": self.contract_version, "reusable": self.reusable}
    @staticmethod
    def from_dict(d):
        return IntegrationPlan(d['operation_family'], [ApiStep.from_dict(x) for x in d['steps']],
                               int(d['contract_version']), bool(d.get('reusable', True)))

@dataclass
class Usage:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0

@dataclass
class Planned:
    plan: IntegrationPlan
    usage: Usage = field(default_factory=Usage)
    raw_text: str = ''

@dataclass
class Capability:
    capability_id: str
    operation_family: str
    version: int
    plan: IntegrationPlan
    contract_version: int
    dependencies: list[str]
    request_schema_hashes: dict[str, str]
    response_schema_hashes: dict[str, str]
    auth_scopes: list[str]
    validation_status: str = 'validated'
    promoted_at: str = ''
    reuse_count: int = 0
    failure_count: int = 0
    superseded_by: str | None = None
    invalidation_reasons: list[str] = field(default_factory=list)

    def to_dict(self):
        d=asdict(self); d['plan']=self.plan.to_dict(); return d
    @staticmethod
    def from_dict(d):
        q=dict(d); q['plan']=IntegrationPlan.from_dict(q['plan']); return Capability(**q)

def stable_hash(obj: Any) -> str:
    data=json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(data).hexdigest()
