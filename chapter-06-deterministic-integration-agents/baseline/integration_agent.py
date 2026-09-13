from common import now_ms, usage_dict
from smart_agent.validation import validate_plan, audit_plan
from integration.execution import execute_plan

class BaselineIntegrationAgent:
    def __init__(self,planner): self.planner=planner
    def handle(self,req,contract,env):
        t=now_ms(); planned=self.planner.plan(req,contract); v=validate_plan(planned.plan,req,contract)
        err=None; ex=None
        try:
            if not v.ok: raise ValueError(str(v.reasons))
            ex=execute_plan(planned.plan,req,contract,env)
        except Exception as e: err=f'{type(e).__name__}: {e}'
        audit=audit_plan(planned.plan,req,contract); ok=audit.ok and err is None
        return {'ok':ok,'audited_correct':ok,'audit_reasons':audit.reasons,'path':'REASONING','llm_calls':1,'usage':usage_dict(planned.usage),'latency_ms':now_ms()-t,'plan':planned.plan.to_dict(),'execution':ex,'error':err,'api_calls':len(planned.plan.steps) if ex else 0}
