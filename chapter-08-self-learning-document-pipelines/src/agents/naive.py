from .common import AgentBase
from src.capabilities.compiler import deterministic_extract
from src.documents.contracts import required_fields
from src.validation.runtime import validate
class NaiveAgent(AgentBase):
    def __init__(self,planner): super().__init__(planner); self.rules={}
    def process(self,text,req):
        fam=req['family_id']
        if fam not in self.rules:
            x=self.llm(text,req); self.rules[fam]=required_fields(fam,req['contract_version'])
            return {'routing_path':'initial_acquisition','llm_called':True,'capability_id':fam,'capability_version':1,'compatibility_checks':{},'fields':x['fields'],'semantic_label':x.get('semantic_label'),'runtime_validation':validate(x['fields'],self.rules[fam]),'usage':x['usage'],'cost':x['cost'],'response_id':x.get('response_id'),'planner_latency_ms':x.get('planner_latency_ms',0)}
        fields=deterministic_extract(text,self.rules[fam],fam,'V1'); val=validate(fields,self.rules[fam])
        if req['reasoning_required']:
            x=self.llm(text,req); sem=x.get('semantic_label'); usage=x['usage']; cost=x['cost']; rid=x.get('response_id'); pl=x.get('planner_latency_ms',0); path='reasoning_required'
        else: sem=None; usage={'input_tokens':0,'output_tokens':0,'cached_input_tokens':0,'reasoning_tokens':0}; cost=0.0; rid=None; pl=0; path='naive_reuse'
        return {'routing_path':path,'llm_called':req['reasoning_required'],'capability_id':fam,'capability_version':1,'compatibility_checks':{},'fields':fields,'semantic_label':sem,'runtime_validation':val,'usage':usage,'cost':cost,'response_id':rid,'planner_latency_ms':pl}
