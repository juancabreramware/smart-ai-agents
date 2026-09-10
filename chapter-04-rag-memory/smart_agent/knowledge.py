from __future__ import annotations
from pathlib import Path
import re, json
from .common import ROOT, stable_hash, tokenize

class KnowledgeBase:
    def __init__(self,version:str): self.version=version; self.root=ROOT/'knowledge_base'/version; self.chunks=self._load()
    def _load(self):
        out=[]
        for p in sorted(self.root.glob('*.md')):
            text=p.read_text(encoding='utf-8')
            matches=list(re.finditer(r'<!-- fact:([^>]+) -->\s*\n([^\n]+)',text))
            for m in matches:
                body=m.group(2).strip(); out.append({'document':p.name,'fact_id':m.group(1).strip(),'text':body,'content_hash':stable_hash(body),'source_version':self.version})
        return out
    def by_fact(self,fact_id): return next((x for x in self.chunks if x['fact_id']==fact_id),None)
    def retrieve(self,query:str,k=5):
        qt=set(tokenize(query)); scored=[]
        for c in self.chunks:
            ct=set(tokenize(c['text']+' '+c['fact_id'].replace('_',' '))); score=len(qt&ct)/(len(qt|ct) or 1)
            scored.append((score,c))
        return [c for _,c in sorted(scored,key=lambda x:x[0],reverse=True)[:k]]
    def ground_truth(self): return json.loads((ROOT/'knowledge_base'/'ground_truth'/f'{self.version}.json').read_text())
