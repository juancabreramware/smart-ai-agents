from common import now_ms, usage_dict
from smart_agent.validation import validate_plan, audit_plan
from integration.execution import execute_plan

class NaiveIntegrationCache:
    def __init__(self,planner): self.planner=planner; self.cache={}
    def handle(self,req,contract,env):
        t=now_ms(); f=req['operation_family']
        if req.get('reuse_allowed',True) and f in self.cache:
            plan=self.cache[f]
            stale=not validate_plan(plan,req,contract).ok; stale_reasons=validate_plan(plan,req,contract).reasons
            err=None; ex=None
            try: ex=execute_plan(plan,req,contract,env)
            except Exception as e: err=f'{type(e).__name__}: {e}'
            audit=audit_plan(plan,req,contract); ok=audit.ok and err is None
            return {'ok':ok,'audited_correct':ok,'audit_reasons':audit.reasons,'path':'CACHE','llm_calls':0,'usage':{'input_tokens':0,'cached_input_tokens':0,'output_tokens':0,'cost':0.0},'latency_ms':now_ms()-t,'plan':plan.to_dict(),'execution':ex,'error':err,'incorrect_stale_reuse':stale or not ok,'stale_reuse_reasons':stale_reasons,'api_calls':len(plan.steps) if ex else 0}
        planned=self.planner.plan(req,contract); v=validate_plan(planned.plan,req,contract); err=None; ex=None
        try:
            if not v.ok: raise ValueError(str(v.reasons))
            ex=execute_plan(planned.plan,req,contract,env)
            if req.get('reuse_allowed',True): self.cache[f]=planned.plan
        except Exception as e: err=f'{type(e).__name__}: {e}'
        audit=audit_plan(planned.plan,req,contract); ok=audit.ok and err is None
        return {'ok':ok,'audited_correct':ok,'audit_reasons':audit.reasons,'path':'RAG_REASONING','llm_calls':1,'usage':usage_dict(planned.usage),'latency_ms':now_ms()-t,'plan':planned.plan.to_dict(),'execution':ex,'error':err,'incorrect_stale_reuse':False,'stale_reuse_reasons':[],'api_calls':len(planned.plan.steps) if ex else 0}
