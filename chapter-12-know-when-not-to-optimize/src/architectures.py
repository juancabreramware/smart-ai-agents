from __future__ import annotations
from dataclasses import asdict
from .models import OptimizationCase
from .scoring import ground_truth,is_correct
from .capabilities import promote,execute
from .cost_model import deterministic_cost,assigned_promotion_cost
from .optimizer import decide

def _row(r,expected,actual,route,usage,overhead,stale=False,extra=None):
    d={"request_id":r.request_id,"sequence":r.sequence,"family":r.family,"version":r.version,"expected":asdict(expected),"actual":asdict(actual),"correct":is_correct(expected,actual),"route":route,"llm_called":usage is not None,"input_tokens":usage.input_tokens if usage else 0,"output_tokens":usage.output_tokens if usage else 0,"provider_cost_micro":usage.provider_cost_micro if usage else 0,"optimization_overhead_micro":overhead,"stale_reuse":bool(stale)}
    if extra:d.update(extra)
    return d

class AlwaysReason:
    name="always_reason"
    def __init__(self,provider):self.provider=provider
    def handle(self,r):
        expected=ground_truth(r); actual,u=self.provider.reason(r); return _row(r,expected,actual,"reason",u,0)

class AlwaysOptimize:
    name="always_optimize"
    def __init__(self,provider):self.provider=provider;self.caps={}
    def handle(self,r):
        expected=ground_truth(r);cap=self.caps.get(r.family)
        if cap and cap.compatible(r):return _row(r,expected,execute(cap,r),"deterministic_reuse",None,deterministic_cost(r.family))
        actual,u=self.provider.reason(r);overhead=0;route="reason"
        if r.family!="ambiguous_judgment":
            relearn=cap is not None;cap=promote(r,f"always-{r.family}-{r.sequence}",relearning=relearn);self.caps[r.family]=cap
            overhead=assigned_promotion_cost(r.family,relearn);route="relearn_and_promote" if relearn else "reason_and_promote"
        return _row(r,expected,actual,route,u,overhead)

class SmartSelective:
    name="smart"
    def __init__(self,provider):
        self.provider=provider;self.caps={};self.cases={};self.last_versions={};self.case_events=[];self.capability_events=[]
    def _record_case(self,r,case,post=False):
        self.case_events.append({"sequence":r.sequence,"family":r.family,"decision":case.decision,"decision_reason":case.decision_reason,"observed_count":case.observed_count,"future_reuse_estimate":case.future_reuse_estimate,"expected_reuse_value_micro":case.expected_reuse_value_micro,"expected_optimization_cost_micro":case.expected_optimization_cost_micro,"llm_called":True,"post_promotion_reevaluation":post})
    def _update_reason_cost(self,case,u,family):
        case.reasoning_cost_total_micro+=u.provider_cost_micro
        reason_calls=sum(1 for e in self.case_events if e.get("family")==family and e.get("llm_called"))+1
        case.reasoning_cost_estimate_micro=case.reasoning_cost_total_micro//max(1,reason_calls)
    def handle(self,r):
        expected=ground_truth(r);case=self.cases.setdefault(r.family,OptimizationCase(r.family))
        old_version=self.last_versions.get(r.family)
        if old_version is not None and old_version!=r.version:case.drift_events_observed+=1
        self.last_versions[r.family]=r.version;case.observed_count+=1;case.eligible_reuse_count+=1
        cap=self.caps.get(r.family)
        if cap and cap.compatible(r):
            return _row(r,expected,execute(cap,r),"deterministic_reuse",None,deterministic_cost(r.family),False,{"optimization_decision":"PROMOTED"})
        if cap and not cap.compatible(r):
            actual,u=self.provider.reason(r);self._update_reason_cost(case,u,r.family);decide(case,r.family,r.sequence);self._record_case(r,case,True)
            if case.decision=="PROMOTE":
                newcap=promote(r,f"smart-{r.family}-{r.sequence}",relearning=True);self.caps[r.family]=newcap
                overhead=assigned_promotion_cost(r.family,True);self.capability_events.append({"sequence":r.sequence,"family":r.family,"event":"RELEARN","version":r.version,"cost_micro":overhead})
                return _row(r,expected,actual,"relearn_and_promote",u,overhead,False,{"optimization_decision":"PROMOTE","optimization_reason":case.decision_reason})
            # Critical v1.0.3 behavior: a drifted capability that no longer clears
            # economics is retired. Reason now; keep gathering evidence; do not pay
            # acquisition/validation/maintenance for a replacement.
            del self.caps[r.family]
            self.capability_events.append({"sequence":r.sequence,"family":r.family,"event":"RETIRE","version":r.version,"cost_micro":0,"reason":case.decision_reason})
            return _row(r,expected,actual,"reason_after_drift_no_relearn",u,0,False,{"optimization_decision":case.decision,"optimization_reason":case.decision_reason})
        actual,u=self.provider.reason(r);self._update_reason_cost(case,u,r.family);decide(case,r.family,r.sequence);self._record_case(r,case,False)
        overhead=0;route="reason"
        if case.decision=="PROMOTE":
            newcap=promote(r,f"smart-{r.family}-{r.sequence}",False);self.caps[r.family]=newcap;overhead=assigned_promotion_cost(r.family,False);route="reason_and_promote"
            self.capability_events.append({"sequence":r.sequence,"family":r.family,"event":"PROMOTE","version":r.version,"cost_micro":overhead})
        return _row(r,expected,actual,route,u,overhead,False,{"optimization_decision":case.decision,"optimization_reason":case.decision_reason})

