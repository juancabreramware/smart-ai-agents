from __future__ import annotations
import time
from smart_agent.knowledge import KnowledgeBase
from smart_agent.providers import Reasoner,Embeddings,cost
from smart_agent.settings import Settings
from smart_agent.common import RunResult
from smart_agent.validation import answer_correct
class BaselineRAGAgent:
    def __init__(self,settings=None): self.s=settings or Settings();self.reasoner=Reasoner(self.s);self.emb=Embeddings(self.s)
    def _facts(self,intent): return {'enterprise_support_in_eu':['enterprise_support_level','eu_regions'],'professional_slack_and_support':['slack_integration_plans','professional_support_level']}.get(intent,[intent])
    def run(self,r):
        t=time.perf_counter();kb=KnowledgeBase(r['source_version']); _,eu=self.emb.embed(r['query']); evidence=[]
        for fid in self._facts(r['canonical_intent']):
            c=kb.by_fact(fid)
            if c:evidence.append(c)
        if not evidence:evidence=kb.retrieve(r['query'],5)
        ans,lu=self.reasoner.answer(r['query'],r['canonical_intent'],evidence,kb.ground_truth(),r.get('llm_required_by_policy',False))
        lu.embedding_calls+=eu.embedding_calls;lu.embedding_tokens+=eu.embedding_tokens
        correct=answer_correct(ans,r['expected'],r['query']); routing=(r.get('llm_required_by_policy') and lu.llm_calls==1) or not r.get('llm_required_by_policy')
        return RunResult(r['query_id'],'baseline',r['source_version'],r['query'],r['canonical_intent'],'RAG_REASONING',ans,r['expected'],correct,routing,[x['document'] for x in evidence],(time.perf_counter()-t)*1000,lu.__dict__,cost(lu,self.s),['RETRIEVE','REASON','VALIDATE'],False)
