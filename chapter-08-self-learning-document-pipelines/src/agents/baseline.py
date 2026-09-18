from .common import AgentBase
from src.documents.contracts import required_fields
from src.validation.runtime import validate
class BaselineAgent(AgentBase):
    def process(self,text,req):
        x=self.llm(text,req); val=validate(x['fields'],required_fields(req['family_id'],req['contract_version']))
        return {'routing_path':'reasoning','llm_called':True,'capability_id':None,'capability_version':None,'compatibility_checks':{},'fields':x['fields'],'semantic_label':x.get('semantic_label'),'runtime_validation':val,'usage':x['usage'],'cost':x['cost'],'response_id':x.get('response_id'),'planner_latency_ms':x.get('planner_latency_ms',0)}
