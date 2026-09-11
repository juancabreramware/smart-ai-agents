from __future__ import annotations
from dataclasses import dataclass, field, asdict
from copy import deepcopy
import hashlib, json
from workflows.schema import WorkflowPlan
from workflows.ground_truth import DEPENDENCIES

@dataclass
class Capability:
    capability_id:str
    workflow_family:str
    version:int
    plan:dict
    dependencies:list[str]
    policy_version:int
    integration_contract_version:int
    policy_hash:str
    validation_status:str="VALID"
    reuse_count:int=0
    failure_count:int=0
    superseded_by:str|None=None

def policy_hash(policy):
    return hashlib.sha256(json.dumps(policy,sort_keys=True).encode()).hexdigest()

class CapabilityRegistry:
    def __init__(self): self.items:dict[str,list[Capability]]={}
    def active(self,family):
        xs=self.items.get(family,[])
        return next((x for x in reversed(xs) if x.validation_status=="VALID" and not x.superseded_by),None)
    def promote(self,plan:WorkflowPlan,policy:dict):
        xs=self.items.setdefault(plan.workflow_family,[])
        version=len(xs)+1
        cap=Capability(
            capability_id=f"{plan.workflow_family}_v{version}",workflow_family=plan.workflow_family,
            version=version,plan=plan.to_dict(),dependencies=sorted(DEPENDENCIES.get(plan.workflow_family,set())),
            policy_version=policy["version"],integration_contract_version=policy["integration_contract_version"],
            policy_hash=policy_hash(policy)
        )
        old=self.active(plan.workflow_family)
        if old: old.superseded_by=cap.capability_id; old.validation_status="SUPERSEDED"
        xs.append(cap); return cap
    def invalidate_changed(self, changed_dependencies:list[str]):
        changed=set(changed_dependencies); invalidated=[]
        for xs in self.items.values():
            for cap in xs:
                if cap.validation_status=="VALID" and changed.intersection(cap.dependencies):
                    cap.validation_status="INVALID"
                    invalidated.append(cap.capability_id)
        return invalidated
    def dump(self):
        return {k:[asdict(x) for x in v] for k,v in self.items.items()}
