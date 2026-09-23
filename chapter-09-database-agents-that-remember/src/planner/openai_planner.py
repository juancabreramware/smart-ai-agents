from __future__ import annotations
import json,time
from openai import OpenAI
from .schemas import OUTPUT_SCHEMA
from src.database.queries import QUERIES
class OpenAIPlanner:
    def __init__(self,model='gpt-5.6-sol',reasoning_effort='medium',pricing=None):
        self.client=OpenAI(); self.model=model; self.reasoning_effort=reasoning_effort; self.pricing=pricing or {'input_per_million':4.0,'cached_input_per_million':0.4,'output_per_million':20.0}
    def plan(self,req):
        canonical=QUERIES[(req['query_family'],req['contract_version'])]
        prompt=f"""You are generating a read-only parameterized SQL capability for a controlled synthetic benchmark.
Family: {req['query_family']}
Contract: {req['contract_version']}
Required parameters: {list(req['parameters'])}
Authoritative database contract supplies this canonical SQL shape for the family; preserve its semantics and named parameters exactly:
{canonical}
Question: {req['question']}
Semantic note: {req.get('semantic_note','none')}
Return the SQL template and, only when the request says semantic reasoning is required, classify the note as one of none,demand_decline,fulfillment_risk,payment_risk,supplier_risk,other. Otherwise semantic_label must be null."""
        t=time.perf_counter(); r=self.client.responses.create(model=self.model,reasoning={'effort':self.reasoning_effort},input=prompt,text={'format':{'type':'json_schema','name':'chapter9_query_capability','schema':OUTPUT_SCHEMA,'strict':True}}); ms=(time.perf_counter()-t)*1000
        obj=json.loads(r.output_text); u=r.usage; inp=getattr(u,'input_tokens',0); out=getattr(u,'output_tokens',0); det=getattr(u,'input_tokens_details',None); cached=getattr(det,'cached_tokens',0) if det else 0; od=getattr(u,'output_tokens_details',None); reasoning=getattr(od,'reasoning_tokens',0) if od else 0
        cost=((inp-cached)*self.pricing['input_per_million']+cached*self.pricing['cached_input_per_million']+out*self.pricing['output_per_million'])/1_000_000
        return {**obj,'usage':{'input_tokens':inp,'output_tokens':out,'cached_input_tokens':cached,'reasoning_tokens':reasoning},'cost':cost,'planner_latency_ms':ms,'response_id':r.id}
