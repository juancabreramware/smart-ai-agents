from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Any
from .common import cosine

@dataclass
class Memory:
    memory_id:str; canonical_intent:str; query_family:str; exemplar_query:str; embedding:list[float]; answer:dict
    source_refs:list[dict]; confidence:float; validation_status:str='validated'; reuse_count:int=0; source_version:str='v1'

class MemoryStore:
    def __init__(self): self.items:dict[str,Memory]={}
    def get(self,intent): return self.items.get(intent)
    def put(self,m:Memory): self.items[m.canonical_intent]=m
    def candidate(self,intent,embedding,threshold):
        m=self.items.get(intent)
        if not m: return None,0.0
        sim=cosine(m.embedding,embedding)
        # canonical intent is primary; embedding is supporting confidence, not validity
        return (m,sim) if sim>=threshold or m.canonical_intent==intent else (None,sim)
