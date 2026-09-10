from __future__ import annotations
import json, time
from .common import Usage, local_embedding
from .settings import Settings

class Embeddings:
    def __init__(self,s:Settings): self.s=s
    def embed(self,text:str):
        if self.s.embeddings=='local': return local_embedding(text),Usage(embedding_calls=1)
        from openai import OpenAI
        c=OpenAI(api_key=self.s.api_key); r=c.embeddings.create(model=self.s.embedding_model,input=text)
        tok=getattr(r.usage,'total_tokens',0) if getattr(r,'usage',None) else 0
        return r.data[0].embedding,Usage(embedding_calls=1,embedding_tokens=tok)

class Reasoner:
    def __init__(self,s:Settings): self.s=s

    @staticmethod
    def _canonical_answer_schema(intent:str):
        integer_value={
            'starter_price_monthly','professional_price_monthly','annual_discount_percentage',
            'starter_api_limit_hourly','professional_api_limit_hourly','backup_retention_days',
            'application_log_retention_days','deleted_account_retention_days','enterprise_audit_log_retention_days'
        }
        string_value={
            'starter_support_level','professional_support_level','enterprise_support_level',
            'cancellation_effective_time','sso_saml_plan'
        }
        array_value={'eu_regions','slack_integration_plans'}
        if intent in integer_value:
            return {'type':'object','properties':{'value':{'type':'integer'}},'required':['value'],'additionalProperties':False}
        if intent in string_value:
            return {'type':'object','properties':{'value':{'type':'string'}},'required':['value'],'additionalProperties':False}
        if intent in array_value:
            return {'type':'object','properties':{'value':{'type':'array','items':{'type':'string'}}},'required':['value'],'additionalProperties':False}
        if intent=='enterprise_support_in_eu':
            return {'type':'object','properties':{'support':{'type':'string'},'regions':{'type':'array','items':{'type':'string'}}},'required':['support','regions'],'additionalProperties':False}
        if intent=='professional_slack_and_support':
            return {'type':'object','properties':{'slack_available':{'type':'boolean'},'support':{'type':'string'}},'required':['slack_available','support'],'additionalProperties':False}
        if intent in {'regulated_financial_company_suitability','plan_recommendation_for_company'}:
            return {'type':'object','properties':{'decision':{'type':'string','enum':['reasoning_required']}},'required':['decision'],'additionalProperties':False}
        raise ValueError(f'No canonical answer schema for intent: {intent}')

    def answer(self,query,intent,evidence,ground_truth,reasoning_required=False):
        if self.s.provider=='mock':
            if reasoning_required: ans={'decision':'reasoning_required'}
            elif intent=='enterprise_support_in_eu': ans={'support':ground_truth['enterprise_support_level'],'regions':ground_truth['eu_regions']}
            elif intent=='professional_slack_and_support': ans={'slack_available':'Professional' in ground_truth['slack_integration_plans'],'support':ground_truth['professional_support_level']}
            else: ans={'value':ground_truth[intent]}
            # deterministic pseudo usage so mock reports are useful but not claimed as measured model economics
            inp=max(1,(len(query)+sum(len(x['text']) for x in evidence))//4); out=max(1,len(json.dumps(ans))//4)
            return ans,Usage(input_tokens=inp,output_tokens=out,llm_calls=1)
        from openai import OpenAI
        client=OpenAI(api_key=self.s.api_key)
        context='\n'.join(f"[{x['document']}#{x['fact_id']}] {x['text']}" for x in evidence)
        answer_schema=self._canonical_answer_schema(intent)
        schema={
            'type':'object',
            'properties':{
                'answer':answer_schema,
                'sources':{'type':'array','items':{'type':'string'}}
            },
            'required':['answer','sources'],
            'additionalProperties':False
        }
        prompt=f"""Answer using only the evidence. The response schema defines the canonical benchmark representation for intent {intent}; preserve that representation exactly. Do not rename fields, add units, wrap values in explanatory strings, or add extra answer fields. If the schema requires decision=reasoning_required, return that decision rather than making the judgment yourself.\nQuestion: {query}\nEvidence:\n{context}"""
        r=client.responses.create(model=self.s.model,input=prompt,text={'format':{'type':'json_schema','name':'chapter4_answer','schema':schema,'strict':True}})
        obj=json.loads(r.output_text); u=getattr(r,'usage',None); inp=getattr(u,'input_tokens',0) if u else 0; out=getattr(u,'output_tokens',0) if u else 0
        cached=0
        det=getattr(u,'input_tokens_details',None) if u else None
        if det: cached=getattr(det,'cached_tokens',0) or 0
        return obj['answer'],Usage(input_tokens=inp,cached_input_tokens=cached,output_tokens=out,llm_calls=1)

def cost(usage:Usage,s:Settings):
    uncached=max(0,usage.input_tokens-usage.cached_input_tokens)
    return uncached/1e6*s.input_per_m + usage.cached_input_tokens/1e6*s.cached_input_per_m + usage.output_tokens/1e6*s.output_per_m + usage.embedding_tokens/1e6*s.embedding_per_m
