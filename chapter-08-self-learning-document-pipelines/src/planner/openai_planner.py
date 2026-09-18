from __future__ import annotations
import json,time
from openai import OpenAI
from src.documents.contracts import required_fields
from src.planner.schemas import extraction_response_schema, validate_strict_schema
class OpenAIPlanner:
    def __init__(self,model='gpt-5.6-sol',reasoning_effort='medium',pricing=None):
        self.client=OpenAI(); self.model=model; self.reasoning_effort=reasoning_effort; self.pricing=pricing or {'input_per_million':4.0,'cached_input_per_million':0.4,'output_per_million':20.0}
    def extract(self,text,family,version,reasoning_required=False,expected=None):
        req=required_fields(family,version)
        schema=extraction_response_schema(family,req)
        validate_strict_schema(schema)
        prompt=f"Extract this synthetic HarborPoint document. Expected family hint: {family}. Contract: {version}. Required fields: {req}. Return exact values from the document; do not invent values. If semantic reasoning is required, classify EXCEPTION_NOTE as one of none, pricing_dispute, quantity_dispute, address_exception, tax_exception, other; otherwise semantic_label must be null.\n\n{text}"
        t=time.perf_counter(); r=self.client.responses.create(model=self.model,reasoning={'effort':self.reasoning_effort},input=prompt,text={'format':{'type':'json_schema','name':'chapter8_extraction','schema':schema,'strict':True}}); ms=(time.perf_counter()-t)*1000
        obj=json.loads(r.output_text); u=r.usage
        inp=getattr(u,'input_tokens',0) or 0; out=getattr(u,'output_tokens',0) or 0
        details=getattr(u,'input_tokens_details',None); cached=getattr(details,'cached_tokens',0) if details else 0
        od=getattr(u,'output_tokens_details',None); reasoning=getattr(od,'reasoning_tokens',0) if od else 0
        cost=((inp-cached)*self.pricing['input_per_million']+cached*self.pricing['cached_input_per_million']+out*self.pricing['output_per_million'])/1_000_000
        return {**obj,'usage':{'input_tokens':inp,'output_tokens':out,'cached_input_tokens':cached,'reasoning_tokens':reasoning},'cost':cost,'response_id':r.id,'planner_latency_ms':ms}
