class AgentBase:
    def __init__(self,planner,db_path,schema_fp): self.planner=planner; self.db_path=db_path; self.schema_fp=schema_fp
    def llm(self,req): return self.planner.plan(req)
