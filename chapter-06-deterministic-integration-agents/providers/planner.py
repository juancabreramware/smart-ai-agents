from __future__ import annotations
import json, os, time
from dotenv import load_dotenv
from integration.schema import IntegrationPlan, Planned, Usage
from integration.ground_truth import canonical_plan
from integration.normalization import canonicalize_plan
load_dotenv()

PLAN_SCHEMA={
  'type':'object','additionalProperties':False,'required':['operation_family','contract_version','reusable','steps'],
  'properties':{
    'operation_family':{'type':'string'},'contract_version':{'type':'integer'},'reusable':{'type':'boolean'},
    'steps':{'type':'array','items':{'type':'object','additionalProperties':False,'required':['api','operation','parameter_map','constants','auth_scope'],
      'properties':{
        'api':{'type':'string'},'operation':{'type':'string'},'auth_scope':{'type':'string'},
        'parameter_map':{'type':'array','items':{'type':'object','additionalProperties':False,'required':['source','target'],'properties':{'source':{'type':'string'},'target':{'type':'string'}}}},
        'constants':{'type':'object','additionalProperties':False,'properties':{}}
      }}}
  }
}

class MockPlanner:
    def plan(self,req,contract): return Planned(canonical_plan(req,contract),Usage(),raw_text='mock')

class OpenAIPlanner:
    def __init__(self,model=None):
        from openai import OpenAI
        self.model=model or os.getenv('OPENAI_MODEL','gpt-5.6'); self.client=OpenAI(timeout=float(os.getenv('OPENAI_TIMEOUT_SECONDS','300')))
        self.attempts=int(os.getenv('OPENAI_MAX_ATTEMPTS','2'))
    def _usage(self,r):
        u=getattr(r,'usage',None); inp=int(getattr(u,'input_tokens',0) or 0); out=int(getattr(u,'output_tokens',0) or 0)
        det=getattr(u,'input_tokens_details',None); cached=int(getattr(det,'cached_tokens',0) or 0) if det else 0
        pi=float(os.getenv('OPENAI_INPUT_PRICE_PER_MILLION','4')); pc=float(os.getenv('OPENAI_CACHED_INPUT_PRICE_PER_MILLION','0.4')); po=float(os.getenv('OPENAI_OUTPUT_PRICE_PER_MILLION','20'))
        cost=((inp-cached)*pi+cached*pc+out*po)/1_000_000
        return Usage(inp,cached,out,cost)
    def plan(self,req,contract):
        catalog=json.loads((__import__('pathlib').Path(__file__).resolve().parents[1]/'catalog'/'operation_catalog.json').read_text())
        payload={'request':req,'active_contract':contract,'operation_documentation':catalog[req['operation_family']],'instruction':'Compile the documented operation into the executable schema. Use bare request.args key names in parameter_map.source (for example customer_id, never request.args.customer_id). Include every parameter mapping documented for the active contract version, including conditional parameters such as approval_code when documented. For ambiguous_customer_action, emit the documented agent.clarify_request step rather than an empty steps array, and use an empty string for auth_scope because that local agent action requires no external authorization. Obey the active contract exactly.'}
        last=None
        for i in range(self.attempts):
            try:
                r=self.client.responses.create(model=self.model,
                    instructions='You are an enterprise integration planner. Return a precise executable integration plan that conforms to the supplied JSON schema. Do not invent API fields not present in the active contract.',
                    input=json.dumps(payload,sort_keys=True),
                    text={'format':{'type':'json_schema','name':'integration_plan','strict':True,'schema':PLAN_SCHEMA}}, store=False)
                raw=r.output_text; plan=IntegrationPlan.from_dict(json.loads(raw)); plan=canonicalize_plan(plan,req,contract); return Planned(plan,self._usage(r),raw)
            except Exception as e:
                last=e
                if i+1<self.attempts: time.sleep(2**i)
        raise last
