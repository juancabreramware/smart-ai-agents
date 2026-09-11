from __future__ import annotations
import time
from workflows.schema import WorkflowPlan
from smart_agent.validation import validate_plan, validate_final_state

class SmartWorkflowAgent:
    def __init__(self, planner, registry):
        self.planner=planner; self.registry=registry
    def handle(self,request,policy,env):
        t=time.perf_counter(); family=request["workflow_family"]; events=[]
        if not request.get("reuse_allowed", True):
            pr=self.planner.plan(request,policy)
            vr=validate_plan(pr.plan,request,policy)
            if not vr.ok:
                return {"ok":False,"path":"REASONING_REQUIRED","llm_calls":1,"usage":pr.usage,
                        "events":["PLAN_REJECTED"]+vr.reasons,"latency_ms":(time.perf_counter()-t)*1000}
            env.execute(request["employee_id"],pr.plan,request)
            fv=validate_final_state(env,request,policy)
            return {"ok":fv.ok,"path":"REASONING_REQUIRED","llm_calls":1,"usage":pr.usage,
                    "events":["REASONING_POLICY_BYPASS"],"plan":pr.plan.to_dict(),
                    "final_validation":fv.reasons,"latency_ms":(time.perf_counter()-t)*1000}
        cap=self.registry.active(family)
        if cap:
            plan=WorkflowPlan.from_dict(cap.plan)
            vr=validate_plan(plan,request,policy)
            if vr.ok:
                env.execute(request["employee_id"],plan,request)
                fv=validate_final_state(env,request,policy)
                if fv.ok:
                    cap.reuse_count+=1
                    return {"ok":True,"path":"DETERMINISTIC_REUSE","capability_id":cap.capability_id,
                            "llm_calls":0,"usage":{"input_tokens":0,"cached_input_tokens":0,"output_tokens":0},
                            "events":["CAPABILITY_HIT","CAPABILITY_VALID","DETERMINISTIC_EXECUTION"],
                            "latency_ms":(time.perf_counter()-t)*1000,"plan":plan.to_dict()}
                cap.failure_count+=1; events+=["POSTCONDITION_FAILED"]
            else:
                cap.validation_status="INVALID"; events+=["CAPABILITY_INVALIDATED"]+vr.reasons
        pr=self.planner.plan(request,policy)
        vr=validate_plan(pr.plan,request,policy)
        if not vr.ok:
            return {"ok":False,"path":"REASONING","llm_calls":1,"usage":pr.usage,
                    "events":events+["PLAN_REJECTED"]+vr.reasons,
                    "latency_ms":(time.perf_counter()-t)*1000}
        env.execute(request["employee_id"],pr.plan,request)
        fv=validate_final_state(env,request,policy)
        if not fv.ok:
            return {"ok":False,"path":"REASONING","llm_calls":1,"usage":pr.usage,
                    "events":events+["POSTCONDITION_FAILED"],"final_validation":fv.reasons,
                    "latency_ms":(time.perf_counter()-t)*1000}
        had_prior=bool(self.registry.items.get(family))
        newcap=self.registry.promote(pr.plan,policy)
        path="RELEARNING" if had_prior else "INITIAL_ACQUISITION"
        return {"ok":True,"path":path,"capability_id":newcap.capability_id,"llm_calls":1,
                "usage":pr.usage,"events":events+["VALIDATED","CAPABILITY_PROMOTED"],
                "plan":pr.plan.to_dict(),"latency_ms":(time.perf_counter()-t)*1000}
