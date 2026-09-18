from __future__ import annotations
import json
from pathlib import Path
from .models import ExecutableDocumentCapability
class CapabilityRegistry:
    def __init__(self): self.current={}; self.history=[]
    def get(self,family): return self.current.get(family)
    def promote(self,cap):
        self.current[cap.family_id]=cap; self.history.append(cap.model_dump())
    def invalidate(self,family): self.current.pop(family,None)
    def snapshot(self,path):
        Path(path).write_text(json.dumps({'current':{k:v.model_dump() for k,v in self.current.items()},'history':self.history},indent=2))
