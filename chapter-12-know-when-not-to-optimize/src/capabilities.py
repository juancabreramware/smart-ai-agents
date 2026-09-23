from __future__ import annotations
from dataclasses import dataclass
import hashlib,json
from .models import Request,Answer

@dataclass
class Capability:
    capability_id:str
    family:str
    version:int
    implementation_hash:str
    policy_fingerprint:str
    environment_fingerprint:str
    validated:bool
    acquisition_cost_micro:int
    validation_cost_micro:int
    maintenance_cost_micro:int
    promoted_at:int
    optimization_case_id:str
    operation_id:str
    def compatible(self,r:Request)->bool:
        return self.validated and self.family==r.family and self.version==r.version

def _operation_id(family:str,version:int)->str:
    return f"{family}:v{version}"

def promote(r:Request,case_id:str,relearning:bool=False)->Capability:
    # Closed, trusted deterministic operation registry. No eval/exec/generated Python.
    operation_id=_operation_id(r.family,r.version)
    material=json.dumps({"family":r.family,"version":r.version,"operation":operation_id},sort_keys=True).encode()
    h=hashlib.sha256(material).hexdigest()
    from .cost_model import DEFAULTS
    c=DEFAULTS[r.family]
    return Capability(
        capability_id=f"{r.family}-v{r.version}",family=r.family,version=r.version,
        implementation_hash=h,policy_fingerprint=f"policy-{r.family}-v{r.version}",
        environment_fingerprint="chapter12-runtime-v2",validated=True,
        acquisition_cost_micro=(c.relearning_micro if relearning else c.acquisition_micro),
        validation_cost_micro=c.validation_micro,maintenance_cost_micro=c.maintenance_micro,
        promoted_at=r.sequence,optimization_case_id=case_id,operation_id=operation_id)

def execute(cap:Capability,r:Request)->Answer:
    if not cap.compatible(r): raise ValueError("Capability is not compatible with request")
    p=r.payload; op=cap.operation_id
    # Intentionally independent of scoring.ground_truth(). These are the trusted
    # executable capabilities under test; scoring remains a separate oracle.
    if op=="stable_recurring:v1":
        v=(p["on_hand"]-p["reserved"]) < p["reorder_point"]; return Answer("reorder" if v else "no_action",v)
    if op=="stable_rare:v1":
        v=p["amount"]>=5000 and p["days_open"]>=10; return Answer("escalate" if v else "no_action",v)
    if op in {"volatile_recurring:v1","volatile_recurring:v2","volatile_recurring:v3"}:
        threshold={1:48,2:36,3:30}[r.version]; v=p["age_hours"]>threshold or p["priority"]; return Answer("prioritize" if v else "no_action",v)
    if op=="high_validation_recurring:v1":
        score=round(p["quality"]*.6+p["delivery"]*.4,2); return Answer("review" if score<82 else "approve",score)
    if op=="emerging_pattern:v1":
        v=p["eta_hours"]>p["promised_hours"]+2; return Answer("expedite" if v else "no_action",v)
    raise ValueError(f"No trusted executable capability for {op}")
