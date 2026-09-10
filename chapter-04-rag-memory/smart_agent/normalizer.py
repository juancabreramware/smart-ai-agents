from __future__ import annotations
import re
INTENT_KEYWORDS={
'starter_price_monthly':['starter','price','cost','monthly','fee'],'professional_price_monthly':['professional','price','cost','monthly','fee'],
'annual_discount_percentage':['annual','yearly','discount','save','savings'],'starter_api_limit_hourly':['starter','api','request','limit','quota','hour'],
'professional_api_limit_hourly':['professional','api','request','limit','quota','hour'],'backup_retention_days':['backup','retention','retain','copies','days'],
'application_log_retention_days':['application','app','production','logs','retention','keep'],'deleted_account_retention_days':['deleted','closed','account','data','retention','closure'],
'enterprise_audit_log_retention_days':['enterprise','audit','logs','retention','history'],'starter_support_level':['starter','support'],
'professional_support_level':['professional','support'],'enterprise_support_level':['enterprise','support'],
'eu_regions':['eu','europe','european','region','hosting','location'],'cancellation_effective_time':['cancel','cancellation','service','access','effective'],
'slack_integration_plans':['slack','integration','plans'],'sso_saml_plan':['sso','saml','plan'],
'enterprise_support_in_eu':['enterprise','support','eu','europe'],'professional_slack_and_support':['professional','slack','support'],
'regulated_financial_company_suitability':['regulated','financial','suitable','compliance'],'plan_recommendation_for_company':['best','fit','company','plan','recommend']}

def normalize_query(q:str)->str: return ' '.join(re.findall(r'[a-z0-9]+',q.lower()))
def infer_intent(q:str)->tuple[str,float]:
    toks=set(normalize_query(q).split()); best=('',0.0)
    for intent,keys in INTENT_KEYWORDS.items():
        score=sum(1 for k in keys if k in toks)/max(1,len(keys))
        # specific intents win ties
        score += 0.02 if intent in ('enterprise_support_in_eu','professional_slack_and_support','regulated_financial_company_suitability','plan_recommendation_for_company') else 0
        if score>best[1]: best=(intent,min(score,1.0))
    return best
