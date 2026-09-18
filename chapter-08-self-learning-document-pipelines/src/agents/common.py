from __future__ import annotations
import time
from src.validation.runtime import validate
class AgentBase:
    def __init__(self,planner): self.planner=planner
    def llm(self,text,req): return self.planner.extract(text,req['family_id'],req['contract_version'],req['reasoning_required'],req)
