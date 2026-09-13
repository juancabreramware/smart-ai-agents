from __future__ import annotations
from datetime import datetime, timezone
from integration.schema import Capability
from integration.contracts import schema_hash, dependency
from smart_agent.validation import capability_dependencies

class CapabilityRegistry:
    def __init__(self): self.items={}; self.promotions=0; self.invalidations=0
    def active_for(self,family):
        xs=[x for x in self.items.values() if x.operation_family==family and x.validation_status=='validated' and not x.superseded_by]
        return sorted(xs,key=lambda x:x.version)[-1] if xs else None
    def promote(self, plan, contract, supersedes=None):
        old_versions=[x.version for x in self.items.values() if x.operation_family==plan.operation_family]
        ver=max(old_versions,default=0)+1; cid=f'{plan.operation_family}_v{ver}'
        deps=capability_dependencies(plan); reqh={}; resph={}; scopes=[]
        for s in plan.steps:
            if s.api=='agent': continue
            k=dependency(s.api,s.operation); reqh[k]=schema_hash(contract,s.api,s.operation,'request'); resph[k]=schema_hash(contract,s.api,s.operation,'response'); scopes.append(s.auth_scope)
        cap=Capability(cid,plan.operation_family,ver,plan,int(contract['contract_version']),deps,reqh,resph,sorted(set(scopes)),promoted_at=datetime.now(timezone.utc).isoformat())
        self.items[cid]=cap; self.promotions+=1
        if supersedes and supersedes in self.items: self.items[supersedes].superseded_by=cid
        return cap
    def invalidate(self,cap,reasons):
        if cap.validation_status=='validated':
            cap.validation_status='invalid'; cap.invalidation_reasons=list(reasons); self.invalidations+=1
    def invalidate_for_changes(self,changed_dependencies):
        changed=set(changed_dependencies); out=[]
        for cap in list(self.items.values()):
            if cap.validation_status=='validated' and changed.intersection(cap.dependencies):
                self.invalidate(cap,['contract_dependency_changed']); out.append(cap.capability_id)
        return out
    def snapshot(self): return {k:v.to_dict() for k,v in sorted(self.items.items())}
