from __future__ import annotations
import json, os, time
from dataclasses import dataclass
from workflows.schema import WorkflowPlan, PLAN_JSON_SCHEMA
from workflows.ground_truth import canonical_plan

from dotenv import load_dotenv

load_dotenv()

@dataclass
class PlannerResult:
    plan: WorkflowPlan
    usage: dict
    latency_ms: float
    response_id: str|None=None

class MockPlanner:
    """Zero-cost deterministic planner for architecture tests."""
    def plan(self, request:dict, policy:dict)->PlannerResult:
        t=time.perf_counter()
        p=canonical_plan(request,policy)
        return PlannerResult(p,{"input_tokens":0,"cached_input_tokens":0,"output_tokens":0},(time.perf_counter()-t)*1000,"mock")

class OpenAIPlanner:
    """Real-model planner using the Responses API with JSON Schema Structured Outputs."""
    def __init__(self, model:str|None=None):
        from openai import OpenAI
        self.model=model or os.getenv("OPENAI_MODEL","gpt-5.6")
        self.client=OpenAI(timeout=float(os.getenv("OPENAI_TIMEOUT_SECONDS","180")))

    def plan(self, request:dict, policy:dict)->PlannerResult:
        system = """You are an enterprise workflow planner for the fictional Northstar Manufacturing Group benchmark. Produce exactly one workflow plan that satisfies the current policy and its workflow_requirements. Respect the listed order, prerequisites, request parameters, and operation names. For step args use only group, repository, project, date, template, and email; set unused keys to null. Never invent operations outside the schema. The benchmark validator compares the executable step sequence to frozen ground truth, so do not add helpful but unrequested steps."""
        payload={"request":request,"policy":policy}
        t=time.perf_counter()
        response=self.client.responses.create(
            model=self.model,
            instructions=system,
            input=json.dumps(payload,sort_keys=True),
            text={"format":{"type":"json_schema","name":"workflow_plan","strict":True,"schema":PLAN_JSON_SCHEMA}},
            store=False,
        )
        elapsed=(time.perf_counter()-t)*1000
        value=json.loads(response.output_text)
        u=response.usage
        inp=getattr(u,"input_tokens",0) or 0
        out=getattr(u,"output_tokens",0) or 0
        details=getattr(u,"input_tokens_details",None)
        cached=getattr(details,"cached_tokens",0) if details else 0
        return PlannerResult(WorkflowPlan.from_dict(value),
            {"input_tokens":inp,"cached_input_tokens":cached or 0,"output_tokens":out},
            elapsed,getattr(response,"id",None))
