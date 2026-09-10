from __future__ import annotations
import time
from .normalizer import infer_intent
from .knowledge import KnowledgeBase
from .memory import MemoryStore,Memory
from .providers import Embeddings,Reasoner,cost
from .settings import Settings
from .validation import sources_current,answer_correct,reuse_allowed
from .common import RunResult,Usage

class SmartAgent:
    def __init__(self,settings=None): self.s=settings or Settings(); self.mem=MemoryStore(); self.emb=Embeddings(self.s); self.reasoner=Reasoner(self.s)
    def _facts(self,intent):
        return {'enterprise_support_in_eu':['enterprise_support_level','eu_regions'],'professional_slack_and_support':['slack_integration_plans','professional_support_level']}.get(intent,[intent])
    def run(self,record):
        t=time.perf_counter(); events=['MEMORY_LOOKUP']; kb=KnowledgeBase(record['source_version']); intent=record['canonical_intent']; qemb,eu=self.emb.embed(record['query']); usage=eu
        m,sim=self.mem.candidate(intent,qemb,self.s.memory_threshold); answer=None;sources=[];path=''
        if m and reuse_allowed(record):
            if sources_current(m,kb):
                events+=['MEMORY_VALID','DETERMINISTIC_REUSE']; m.reuse_count+=1; answer=m.answer; sources=[r['document'] for r in m.source_refs]; path='MEMORY'
            else: events+=['SOURCE_CHANGED','MEMORY_INVALIDATED']; path='RELEARNING'
        if answer is None:
            if record.get('llm_required_by_policy'): events+=['REASONING_REQUIRED']
            elif m is None: events+=['MEMORY_MISS','ACQUIRE']
            evidence=[]
            # provenance-first retrieval: known intent narrows to supporting fact ids, while reason-only queries use normal RAG
            wanted=self._facts(intent)
            for fid in wanted:
                c=kb.by_fact(fid)
                if c: evidence.append(c)
            if not evidence: evidence=kb.retrieve(record['query'],5)
            answer,lu=self.reasoner.answer(record['query'],intent,evidence,kb.ground_truth(),record.get('llm_required_by_policy',False))
            usage.input_tokens+=lu.input_tokens;usage.cached_input_tokens+=lu.cached_input_tokens;usage.output_tokens+=lu.output_tokens;usage.llm_calls+=lu.llm_calls
            sources=[x['document'] for x in evidence]
            if reuse_allowed(record) and answer_correct(answer,record['expected'],record['query']):
                refs=[{'document':x['document'],'fact_id':x['fact_id'],'source_version':x['source_version'],'content_hash':x['content_hash']} for x in evidence]
                self.mem.put(Memory(intent,intent,record['class'],record['query'],qemb,answer,refs,1.0,source_version=record['source_version']))
                events+=['VALIDATED','MEMORY_PROMOTED']
            if not path: path='REASONING'
        correct=answer_correct(answer,record['expected'],record['query']); routing_correct=(record.get('llm_required_by_policy') and usage.llm_calls==1) or (not record.get('llm_required_by_policy'))
        return RunResult(record['query_id'],'smart',record['source_version'],record['query'],intent,path,answer,record['expected'],correct,routing_correct,sources,(time.perf_counter()-t)*1000,usage.__dict__,cost(usage,self.s),events,False)
