from dataclasses import dataclass,asdict,field
from typing import Any
@dataclass(frozen=True)
class Contract:
    family:str; version:str; semantic_version:str; operation:str
    dependencies:tuple[str,...]; parameters:dict[str,Any]; policy_fingerprint:str
    environment_fingerprint:str="python-safe-runtime-v1"
@dataclass(frozen=True)
class Request:
    request_id:str; sequence:int; family:str; contract_version:str; inputs:dict[str,Any]
    reasoning_required:bool=False; note:str|None=None; drift_event:bool=False
@dataclass
class Candidate:
    family:str; contract_version:str; operation:str; dependencies:list[str]
    policy_fingerprint:str; environment_fingerprint:str; provenance:dict=field(default_factory=dict)
@dataclass
class Capability:
    capability_id:str; capability_version:int; family:str; contract_version:str; operation:str
    dependencies:tuple[str,...]; policy_fingerprint:str; environment_fingerprint:str
    implementation_hash:str; validation_status:str="validated"; provenance:dict=field(default_factory=dict)
@dataclass
class Usage:
    input_tokens:int=0; output_tokens:int=0; cost_usd:float=0.; latency_ms:float=0.
@dataclass
class ProviderResult:
    output:dict[str,Any]; usage:Usage
@dataclass
class Decision:
    action:str; value:Any; label:str|None=None
