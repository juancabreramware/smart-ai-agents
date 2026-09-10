from smart_agent.knowledge import KnowledgeBase
def test_v2_changes_and_unchanged():
    a=KnowledgeBase('v1');b=KnowledgeBase('v2')
    assert a.by_fact('backup_retention_days')['content_hash']!=b.by_fact('backup_retention_days')['content_hash']
    assert a.by_fact('starter_price_monthly')['content_hash']==b.by_fact('starter_price_monthly')['content_hash']
