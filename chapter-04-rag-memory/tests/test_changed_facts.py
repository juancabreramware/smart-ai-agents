from smart_agent.knowledge import KnowledgeBase

def test_exact_locked_changed_fact_set():
    a,b=KnowledgeBase('v1'),KnowledgeBase('v2')
    changed={x['fact_id'] for x in a.chunks if b.by_fact(x['fact_id']) and x['content_hash'] != b.by_fact(x['fact_id'])['content_hash']}
    assert changed == {'backup_retention_days','starter_api_limit_hourly','enterprise_support_level','eu_regions','annual_discount_percentage'}
