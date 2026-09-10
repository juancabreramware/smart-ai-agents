from smart_agent.providers import Reasoner

def test_simple_fact_contract_uses_value_only():
    s=Reasoner._canonical_answer_schema('backup_retention_days')
    assert s['required']==['value']
    assert s['properties']['value']['type']=='integer'
    assert s['additionalProperties'] is False

def test_compositional_contract_is_canonical():
    s=Reasoner._canonical_answer_schema('enterprise_support_in_eu')
    assert s['required']==['support','regions']
    assert set(s['properties'])=={'support','regions'}
    assert s['additionalProperties'] is False

def test_reasoning_required_contract_is_fixed():
    s=Reasoner._canonical_answer_schema('regulated_financial_company_suitability')
    assert s['properties']['decision']['enum']==['reasoning_required']
