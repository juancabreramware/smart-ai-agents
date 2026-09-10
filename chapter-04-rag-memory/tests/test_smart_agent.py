import json
from smart_agent.common import ROOT
from smart_agent.agent import SmartAgent
from smart_agent.settings import Settings
def rec(intent,ver='v1'):
    w=json.loads((ROOT/'workloads/full.json').read_text());return next(x for x in w if x['canonical_intent']==intent and x['source_version']==ver)
def test_acquire_then_reuse():
    a=SmartAgent(Settings(provider='mock',embeddings='local'));r=rec('backup_retention_days');x=a.run(r);y=a.run(r);assert x.path=='REASONING';assert y.path=='MEMORY';assert y.usage['llm_calls']==0

def test_selective_invalidation_and_relearning():
    a=SmartAgent(Settings(provider='mock',embeddings='local'));v1=rec('backup_retention_days','v1');unch=rec('starter_price_monthly','v1');a.run(v1);a.run(unch)
    v2=rec('backup_retention_days','v2');x=a.run(v2);assert x.path=='RELEARNING';assert x.answer=={'value':45};assert 'MEMORY_INVALIDATED' in x.events
    u2=rec('starter_price_monthly','v2');y=a.run(u2);assert y.path=='MEMORY';assert y.answer=={'value':29}

def test_reasoning_required_never_reuses():
    a=SmartAgent(Settings(provider='mock',embeddings='local'));r=rec('regulated_financial_company_suitability');x=a.run(r);y=a.run(r);assert x.usage['llm_calls']==1 and y.usage['llm_calls']==1
