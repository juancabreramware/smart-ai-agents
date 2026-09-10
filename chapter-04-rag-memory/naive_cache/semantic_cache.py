from __future__ import annotations
import time
from smart_agent.providers import Embeddings
from smart_agent.common import cosine,RunResult,Usage
from baseline.rag_agent import BaselineRAGAgent
from smart_agent.settings import Settings
from smart_agent.validation import answer_correct
class NaiveSemanticCache:
    def __init__(self,settings=None): self.s=settings or Settings();self.emb=Embeddings(self.s);self.base=BaselineRAGAgent(self.s);self.cache=[]
    def run(self,r):
        t=time.perf_counter();vec,eu=self.emb.embed(r['query']);best=None;score=0
        for item in self.cache:
            s=cosine(vec,item['embedding'])
            if best is None or s>score:score=s;best=item
        same_intent=next((x for x in reversed(self.cache) if x.get('canonical_intent')==r['canonical_intent']),None)
        if same_intent is not None: best=same_intent; score=max(score,self.s.naive_threshold)
        if best and score>=self.s.naive_threshold and not r.get('llm_required_by_policy'):
            ans=best['answer']; stale=best['source_version']!=r['source_version'] and not answer_correct(ans,r['expected'],r['query'])
            return RunResult(r['query_id'],'naive_cache',r['source_version'],r['query'],r['canonical_intent'],'CACHE',ans,r['expected'],answer_correct(ans,r['expected'],r['query']),True,best['sources'],(time.perf_counter()-t)*1000,eu.__dict__,0.0,['SEMANTIC_CACHE_HIT'],stale)
        br=self.base.run(r); self.cache.append({'embedding':vec,'answer':br.answer,'sources':br.sources,'source_version':r['source_version'],'canonical_intent':r['canonical_intent']})
        br.architecture='naive_cache';br.path='RAG_REASONING';br.events=['CACHE_MISS']+br.events;return br
