from .common import AgentBase
from src.database.executor import execute,validate_sql
from src.validation.runtime import validate_result
class BaselineAgent(AgentBase):
    def process(self,req):
        x=self.llm(req); sql=x['sql_template']; safety=validate_sql(sql); rows,dbms=execute(self.db_path,sql,req['parameters']); val=validate_result(rows)
        return {'routing_path':'reasoning','llm_called':True,'sql_template':sql,'rows':rows,'semantic_label':x.get('semantic_label'),'runtime_validation':{**val,'sql_safety':safety},'usage':x['usage'],'cost':x['cost'],'planner_latency_ms':x.get('planner_latency_ms',0),'db_latency_ms':dbms,'capability_id':None,'capability_version':None,'compatibility_checks':{}}
