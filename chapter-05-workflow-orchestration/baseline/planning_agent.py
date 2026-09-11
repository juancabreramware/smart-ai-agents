from __future__ import annotations
import time
from smart_agent.validation import validate_plan, validate_final_state

class BaselinePlanningAgent:
    def __init__(self, planner): self.planner=planner
    def handle(self, request, policy, env):
        t=time.perf_counter()
        pr=self.planner.plan(request,policy)
        pv=validate_plan(pr.plan,request,policy)
        if not pv.ok:
            return {"ok":False,"path":"REASONING","plan_validation":pv.reasons,
                    "llm_calls":1,"usage":pr.usage,"latency_ms":(time.perf_counter()-t)*1000}
        env.execute(request["employee_id"],pr.plan,request)
        fv=validate_final_state(env,request,policy)
        return {"ok":fv.ok,"path":"REASONING","plan_validation":[],
                "final_validation":fv.reasons,"llm_calls":1,"usage":pr.usage,
                "plan":pr.plan.to_dict(),"latency_ms":(time.perf_counter()-t)*1000}
