from __future__ import annotations
from dataclasses import asdict
from .models import Request, ValidatedCapability
from .runtime import execute
from .capabilities import compatible, promote, MIN_OBSERVATIONS_TO_PROMOTE

class BaseArchitecture:
    name="base"
    def __init__(self,provider):
        self.provider=provider
        self.registry:dict[str,ValidatedCapability]={}
        self.observations:dict[tuple[str,str],int]={}
        self.events=[]
    def _event(self,r,event,**extra):
        self.events.append({"request_id":r.request_id,"sequence":r.sequence,"wave":r.wave,"family":r.family,"version":r.version,"event":event,**extra})
    def _reason(self,r,route):
        pr=self.provider.reason(r)
        return pr,route
    def on_wave_start(self,wave:int): pass

class StatelessReason(BaseArchitecture):
    name="stateless_reason"
    def handle(self,r):
        pr,route=self._reason(r,"reason_every_time")
        return pr.answer,pr.usage,route,None

class ReuseBase(BaseArchitecture):
    def _observe(self,r):
        k=(r.family,r.version); self.observations[k]=self.observations.get(k,0)+1
        return self.observations[k]
    def handle(self,r):
        obs=self._observe(r)
        cap=self.registry.get(r.family)
        if r.reasoning_required:
            pr,route=self._reason(r,"reasoning_required")
            return pr.answer,pr.usage,route,None
        if cap is not None and not compatible(cap,r):
            cap.invalidation_reason=f"contract_or_environment_changed:{cap.contract_version}->{r.version}"
            self._event(r,"INVALIDATE",capability_id=cap.capability_id,reason=cap.invalidation_reason)
            del self.registry[r.family]; cap=None
        if cap is not None:
            ans=execute(cap.operation,r); cap.reuse_count+=1
            self._event(r,"REUSE",capability_id=cap.capability_id,reuse_count=cap.reuse_count)
            return ans,None,"deterministic_reuse",cap.capability_id
        pr,route=self._reason(r,"reason_new_or_invalidated")
        if obs>=MIN_OBSERVATIONS_TO_PROMOTE:
            cap=promote(r,pr)
            if cap:
                self.registry[r.family]=cap
                self._event(r,"PROMOTE",capability_id=cap.capability_id,operation=cap.operation)
                route="reason_and_promote"
        return pr.answer,pr.usage,route,cap.capability_id if cap else None

class EpisodicReuse(ReuseBase):
    name="episodic_reuse"
    def on_wave_start(self,wave:int):
        if wave>1:
            for cap in list(self.registry.values()):
                self.events.append({"request_id":None,"sequence":None,"wave":wave,"family":cap.family,"version":cap.contract_version,"event":"RESET","capability_id":cap.capability_id})
            self.registry.clear()
            # Evidence inside a wave only; no cross-wave recurrence state.
            self.observations.clear()

class CompoundingSmart(ReuseBase):
    name="compounding_smart"
    # Registry and observation state intentionally persist across waves.
