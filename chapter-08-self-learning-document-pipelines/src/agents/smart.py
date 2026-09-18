from .common import AgentBase
from src.capabilities.models import ExecutableDocumentCapability
from src.capabilities.compatibility import fingerprint,compatible
from src.capabilities.compiler import deterministic_extract
from src.documents.contracts import required_fields
from src.validation.runtime import validate
class SmartAgent(AgentBase):
    def __init__(self,planner,registry): super().__init__(planner); self.registry=registry
    def _learn(self,text,req,path):
        x=self.llm(text,req); fields=x['fields']; val=validate(fields,required_fields(req['family_id'],req['contract_version']))
        if val['ok']:
            old=[h for h in self.registry.history if h['family_id']==req['family_id']]
            cap=ExecutableDocumentCapability(capability_id=req['family_id'],capability_version=len(old)+1,family_id=req['family_id'],family_contract_version=req['contract_version'],required_fields=required_fields(req['family_id'],req['contract_version']),fingerprint=fingerprint(text),provenance={'request_id':req['request_id']})
            self.registry.promote(cap)
        return {'routing_path':path,'llm_called':True,'capability_id':req['family_id'],'capability_version':self.registry.get(req['family_id']).capability_version if self.registry.get(req['family_id']) else None,'compatibility_checks':{},'fields':fields,'semantic_label':x.get('semantic_label'),'runtime_validation':val,'usage':x['usage'],'cost':x['cost'],'response_id':x.get('response_id'),'planner_latency_ms':x.get('planner_latency_ms',0)}
    def process(self,text,req):
        cap=self.registry.get(req['family_id'])
        if not cap: return self._learn(text,req,'initial_acquisition')
        ok,checks=compatible(cap,req['family_id'],req['contract_version'],text)
        if not ok:
            self.registry.invalidate(req['family_id']); return self._learn(text,req,'relearning')
        fields=deterministic_extract(text,cap.required_fields,cap.family_id,cap.family_contract_version); val=validate(fields,cap.required_fields)
        if not val['ok']:
            self.registry.invalidate(req['family_id']); return self._learn(text,req,'relearning')
        if req['reasoning_required']:
            x=self.llm(text,req)
            return {'routing_path':'reasoning_required','llm_called':True,'capability_id':cap.capability_id,'capability_version':cap.capability_version,'compatibility_checks':checks,'fields':fields,'semantic_label':x.get('semantic_label'),'runtime_validation':val,'usage':x['usage'],'cost':x['cost'],'response_id':x.get('response_id'),'planner_latency_ms':x.get('planner_latency_ms',0)}
        return {'routing_path':'deterministic_reuse','llm_called':False,'capability_id':cap.capability_id,'capability_version':cap.capability_version,'compatibility_checks':checks,'fields':fields,'semantic_label':None,'runtime_validation':val,'usage':{'input_tokens':0,'output_tokens':0,'cached_input_tokens':0,'reasoning_tokens':0},'cost':0.0,'response_id':None,'planner_latency_ms':0}
