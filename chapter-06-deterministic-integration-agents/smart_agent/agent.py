from common import now_ms, usage_dict
from smart_agent.validation import validate_plan, validate_capability, audit_plan
from integration.execution import execute_plan

class SmartIntegrationAgent:
    def __init__(self,planner,registry): self.planner=planner; self.registry=registry
    def on_contract_change(self,contract): return self.registry.invalidate_for_changes(contract.get('changed_dependencies',[]))
    def _reason(self,req,contract,env,path,prior=None,promote=True):
        planned=self.planner.plan(req,contract); v=validate_plan(planned.plan,req,contract); err=None; ex=None; cap=None
        try:
            if not v.ok: raise ValueError(str(v.reasons))
            ex=execute_plan(planned.plan,req,contract,env)
            if promote and req.get('reuse_allowed',True) and planned.plan.reusable:
                cap=self.registry.promote(planned.plan,contract,prior.capability_id if prior else None)
        except Exception as e: err=f'{type(e).__name__}: {e}'
        a=audit_plan(planned.plan,req,contract); ok=a.ok and err is None
        return {'ok':ok,'audited_correct':ok,'audit_reasons':a.reasons,'path':path,'llm_calls':1,'usage':usage_dict(planned.usage),'plan':planned.plan.to_dict(),'execution':ex,'error':err,'capability_id':cap.capability_id if cap else None,'api_calls':len(planned.plan.steps) if ex else 0}
    def handle(self,req,contract,env):
        t=now_ms()
        if not req.get('reuse_allowed',True):
            r=self._reason(req,contract,env,'REASONING_REQUIRED',promote=False); r['latency_ms']=now_ms()-t; return r
        cap=self.registry.active_for(req['operation_family'])
        if cap:
            cv=validate_capability(cap,req,contract)
            if cv.ok:
                err=None; ex=None
                try: ex=execute_plan(cap.plan,req,contract,env); cap.reuse_count+=1
                except Exception as e: err=f'{type(e).__name__}: {e}'; cap.failure_count+=1
                a=audit_plan(cap.plan,req,contract); ok=a.ok and err is None
                return {'ok':ok,'audited_correct':ok,'audit_reasons':a.reasons,'path':'DETERMINISTIC_REUSE','llm_calls':0,'usage':{'input_tokens':0,'cached_input_tokens':0,'output_tokens':0,'cost':0.0},'latency_ms':now_ms()-t,'plan':cap.plan.to_dict(),'execution':ex,'error':err,'capability_id':cap.capability_id,'api_calls':len(cap.plan.steps) if ex else 0}
            self.registry.invalidate(cap,cv.reasons)
            r=self._reason(req,contract,env,'RELEARNING',prior=cap,promote=True); r['invalidation_reasons']=cv.reasons; r['latency_ms']=now_ms()-t; return r
        # Distinguish a family that previously existed and was selectively invalidated from first acquisition.
        prior=[x for x in self.registry.items.values() if x.operation_family==req['operation_family'] and x.validation_status=='invalid']
        path='RELEARNING' if prior else 'INITIAL_ACQUISITION'; old=sorted(prior,key=lambda x:x.version)[-1] if prior else None
        r=self._reason(req,contract,env,path,prior=old,promote=True); r['latency_ms']=now_ms()-t; return r
