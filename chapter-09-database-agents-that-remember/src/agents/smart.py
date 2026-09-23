from .common import AgentBase
from src.database.executor import execute,validate_sql
from src.validation.runtime import validate_result
from src.capabilities.models import QueryCapability
from src.capabilities.compatibility import compatible
class SmartAgent(AgentBase):
    def __init__(self,planner,db_path,schema_fp,registry): super().__init__(planner,db_path,schema_fp); self.registry=registry
    def _learn(self,req,path):
        x=self.llm(req); sql=x['sql_template']; safety=validate_sql(sql); rows,dbms=execute(self.db_path,sql,req['parameters']); val=validate_result(rows)
        if safety['ok'] and val['ok']:
            n=1+sum(h['family_id']==req['query_family'] for h in self.registry.history)
            cap=QueryCapability(req['query_family'],n,req['query_family'],req.get('family_contract_version',req['contract_version']),sql,list(req['parameters']),self.schema_fp,provenance={'request_id':req['request_id']}); self.registry.promote(cap)
        cap=self.registry.get(req['query_family'])
        return {'routing_path':path,'llm_called':True,'sql_template':sql,'rows':rows,'semantic_label':x.get('semantic_label'),'runtime_validation':{**val,'sql_safety':safety},'usage':x['usage'],'cost':x['cost'],'planner_latency_ms':x.get('planner_latency_ms',0),'db_latency_ms':dbms,'capability_id':cap.capability_id if cap else None,'capability_version':cap.capability_version if cap else None,'compatibility_checks':{}}
    def process(self,req):
        cap=self.registry.get(req['query_family'])
        if not cap: return self._learn(req,'initial_acquisition')
        ok,checks=compatible(cap,req,self.schema_fp)
        if not ok:
            self.registry.invalidate(req['query_family']); return self._learn(req,'relearning')
        rows,dbms=execute(self.db_path,cap.sql_template,req['parameters']); val=validate_result(rows)
        if not val['ok']:
            self.registry.invalidate(req['query_family']); return self._learn(req,'relearning')
        if req['reasoning_required']:
            x=self.llm(req)
            return {'routing_path':'reasoning_required','llm_called':True,'sql_template':cap.sql_template,'rows':rows,'semantic_label':x.get('semantic_label'),'runtime_validation':val,'usage':x['usage'],'cost':x['cost'],'planner_latency_ms':x.get('planner_latency_ms',0),'db_latency_ms':dbms,'capability_id':cap.capability_id,'capability_version':cap.capability_version,'compatibility_checks':checks}
        return {'routing_path':'deterministic_reuse','llm_called':False,'sql_template':cap.sql_template,'rows':rows,'semantic_label':None,'runtime_validation':val,'usage':{'input_tokens':0,'output_tokens':0,'cached_input_tokens':0,'reasoning_tokens':0},'cost':0.0,'planner_latency_ms':0,'db_latency_ms':dbms,'capability_id':cap.capability_id,'capability_version':cap.capability_version,'compatibility_checks':checks}
