from src.database.queries import QUERIES
class MockPlanner:
    model='mock-planner'
    def plan(self,req):
        return {'sql_template':QUERIES[(req['query_family'],req['contract_version'])],'semantic_label':req.get('semantic_label') if req.get('reasoning_required') else None,'usage':{'input_tokens':0,'output_tokens':0,'cached_input_tokens':0,'reasoning_tokens':0},'cost':0.0,'planner_latency_ms':0}
