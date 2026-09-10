from naive_cache.semantic_cache import NaiveSemanticCache
from smart_agent.settings import Settings

def test_naive_cache_can_return_stale_answer():
    a=NaiveSemanticCache(Settings(provider='mock',embeddings='local',naive_threshold=0.0))
    r1={'query_id':'a','source_version':'v1','class':'reusable_fact','canonical_intent':'backup_retention_days','query':'How long are backups retained?','expected':{'value':30},'expected_sources':['data-retention.md'],'deterministic_memory_reuse_allowed':True,'llm_required_by_policy':False}
    r2=dict(r1,query_id='b',source_version='v2',query='What is the backup retention period?',expected={'value':45})
    a.run(r1);x=a.run(r2);assert x.path=='CACHE';assert x.correct is False;assert x.stale_reuse is True

def test_naive_cache_unchanged_fact_across_versions_is_not_stale():
    a=NaiveSemanticCache(Settings(provider='mock',embeddings='local',naive_threshold=0.0))
    r1={'query_id':'a','source_version':'v1','class':'reusable_fact','canonical_intent':'starter_price_monthly','query':'What does Starter cost per month?','expected':{'value':29},'expected_sources':['pricing.md'],'deterministic_memory_reuse_allowed':True,'llm_required_by_policy':False}
    r2=dict(r1,query_id='b',source_version='v2',query='How much is the Starter plan?')
    a.run(r1); x=a.run(r2)
    assert x.path=='CACHE'; assert x.correct is True; assert x.stale_reuse is False
