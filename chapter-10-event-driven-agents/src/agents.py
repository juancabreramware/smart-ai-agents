from __future__ import annotations
import time
from .models import Observation, EvidenceRow, Decision
from .contracts import get_contract
from .ground_truth import authoritative_decision
from .sentinels import SentinelRegistry, compatible, evaluate_with_sentinel
from .provider import ReasoningProvider

def _row(run_id,arch,obs,route,reason,compat,sentinel,llm,provider,usage,decision,whash,stale=False):
    truth=authoritative_decision(obs)
    correct=(decision.action==truth.action and (truth.label is None or decision.label==truth.label))
    fp=truth.action=="no_action" and decision.action!="no_action"
    fn=truth.action!="no_action" and decision.action=="no_action"
    c=get_contract(obs.family,obs.contract_version)
    return EvidenceRow(
        run_id,arch,obs.observation_id,obs.sequence,obs.entity_id,obs.family,obs.contract_version,
        route,reason,compat,getattr(sentinel,"sentinel_id",None),getattr(sentinel,"sentinel_version",None),
        llm,provider.name,provider.model,usage.input_tokens,usage.output_tokens,usage.cost_usd,usage.latency_ms,
        usage.latency_ms,truth.action,decision.action,truth.label,decision.label,correct,fp,fn,stale,False,
        whash,c.fingerprint()
    )

class BaselineAgent:
    def __init__(self,provider): self.provider=provider
    def process(self,run_id,obs,whash):
        d,u=self.provider.decide(obs,"baseline_full_observation_reasoning")
        return _row(run_id,"baseline",obs,"baseline_reasoning","reason_every_observation","n/a",None,True,self.provider,u,d,whash)

class SmartAgent:
    def __init__(self,provider):
        self.provider=provider
        self.registry=SentinelRegistry()

    def process(self,run_id,obs,whash):
        c=get_contract(obs.family,obs.contract_version)
        s=self.registry.get(obs.family)
        if s is None:
            d,u=self.provider.decide(obs,"initial_monitor_acquisition")
            s=self.registry.promote(obs.family,c)
            return _row(run_id,"smart",obs,"initial_acquisition","no_validated_sentinel","acquired",s,True,self.provider,u,d,whash)

        ok,reason=compatible(s,c,obs)
        if not ok:
            d,u=self.provider.decide(obs,"monitor_relearning_after_contract_drift")
            s=self.registry.promote(obs.family,c)
            return _row(run_id,"smart",obs,"relearning",reason,"relearned",s,True,self.provider,u,d,whash)

        if obs.reasoning_required:
            d,u=self.provider.decide(obs,"semantic_reasoning_required")
            return _row(run_id,"smart",obs,"reasoning_required","sentinel_escalation","compatible",s,True,self.provider,u,d,whash)

        d=evaluate_with_sentinel(s,obs)
        from .models import ProviderUsage
        return _row(run_id,"smart",obs,"deterministic_reuse","validated_sentinel","compatible",s,False,self.provider,ProviderUsage(),d,whash)

class NaiveAgent:
    def __init__(self,provider):
        self.provider=provider
        self.registry=SentinelRegistry()

    def process(self,run_id,obs,whash):
        # Naive acquires V1 monitor once and never checks contract fingerprints again.
        s=self.registry.get(obs.family)
        if s is None:
            c=get_contract(obs.family,"V1")
            d,u=self.provider.decide(obs,"naive_initial_monitor_acquisition")
            s=self.registry.promote(obs.family,c)
            return _row(run_id,"naive",obs,"initial_acquisition","no_cached_rule","naive_acquired",s,True,self.provider,u,d,whash)

        if obs.reasoning_required:
            d,u=self.provider.decide(obs,"naive_semantic_reasoning_required")
            return _row(run_id,"naive",obs,"reasoning_required","coarse_escalation","unchecked",s,True,self.provider,u,d,whash)

        d=evaluate_with_sentinel(s,obs)
        truth=authoritative_decision(obs)
        stale=obs.contract_version=="V2" and (d.action!=truth.action or d.label!=truth.label)
        from .models import ProviderUsage
        return _row(run_id,"naive",obs,"naive_reuse","unchecked_cached_rule","unchecked",s,False,self.provider,ProviderUsage(),d,whash,stale=stale)
