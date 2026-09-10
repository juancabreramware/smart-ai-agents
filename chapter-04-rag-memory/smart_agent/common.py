from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import hashlib, json, math, re, time

ROOT=Path(__file__).resolve().parents[1]

def canonical_json(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def stable_hash(text:str)->str: return hashlib.sha256(text.encode('utf-8')).hexdigest()
def tokenize(text:str): return re.findall(r"[a-z0-9]+",text.lower())
def cosine(a,b):
    dot=sum(x*y for x,y in zip(a,b)); na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(y*y for y in b))
    return dot/(na*nb) if na and nb else 0.0

def local_embedding(text:str,dims:int=256):
    v=[0.0]*dims
    for tok in tokenize(text):
        h=int(hashlib.sha256(tok.encode()).hexdigest()[:16],16); v[h%dims]+=1.0
    n=math.sqrt(sum(x*x for x in v)) or 1.0
    return [x/n for x in v]

@dataclass
class Usage:
    input_tokens:int=0; cached_input_tokens:int=0; output_tokens:int=0; embedding_tokens:int=0
    llm_calls:int=0; embedding_calls:int=0

@dataclass
class RunResult:
    query_id:str; architecture:str; source_version:str; query:str; canonical_intent:str; path:str
    answer:dict; expected:dict; correct:bool; routing_correct:bool; sources:list[str]
    latency_ms:float; usage:dict; cost_usd:float; events:list[str]; stale_reuse:bool=False
    def to_dict(self): return asdict(self)
