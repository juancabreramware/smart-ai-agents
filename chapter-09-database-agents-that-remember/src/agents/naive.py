from .common import AgentBase
from src.database.executor import execute
from src.validation.runtime import validate_result
class NaiveAgent(AgentBase):
    def __init__(self,planner,db_path,schema_fp): super().__init__(planner,db_path,schema_fp); self.cache={}
    def process(self,req):
        f=req['query_family']; first=f not in self.cache
        if first:
            x=self.llm(req); self.cache[f]=x['sql_template']; path='initial_acquisition'; called=True
        elif req['reasoning_required']:
            x=self.llm(req); path='reasoning_required'; called=True
        else:
            x={'semantic_label':None,'usage':{'input_tokens':0,'output_tokens':0,'cached_input_tokens':0,'reasoning_tokens':0},'cost':0.0,'planner_latency_ms':0}; path='naive_reuse'; called=False
        sql=self.cache[f]; rows,dbms=execute(self.db_path,sql,req['parameters']); val=validate_result(rows)
        return {'routing_path':path,'llm_called':called,'sql_template':sql,'rows':rows,'semantic_label':x.get('semantic_label'),'runtime_validation':val,'usage':x['usage'],'cost':x['cost'],'planner_latency_ms':x.get('planner_latency_ms',0),'db_latency_ms':dbms,'capability_id':f,'capability_version':1,'compatibility_checks':{}}
