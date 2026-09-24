from __future__ import annotations
import json, os
from .models import Request, ProviderResult, Usage, Answer
from .contracts import public_contract, OPERATION_BY_FAMILY, ALLOWED_OPERATIONS

class MockProvider:
    model="deterministic-mock"
    def reason(self,r:Request)->ProviderResult:
        # Mock may use scorer; real provider below has no scoring import/access.
        from .scoring import ground_truth
        return ProviderResult(
            answer=ground_truth(r),
            operation=OPERATION_BY_FAMILY[r.family],
            usage=Usage(input_tokens=620,output_tokens=140),
        )

class OpenAIProvider:
    def __init__(self,model:str|None=None):
        from openai import OpenAI
        self.client=OpenAI()
        self.model=model or os.getenv("CH13_MODEL","gpt-5-mini")

    def reason(self,r:Request)->ProviderResult:
        contract=public_contract(r.family,r.version)
        prompt=(
            "You are solving one operational decision. Use ONLY the current public business contract "
            "and current request. Return JSON only with keys answer and operation. "
            f"Allowed operation for this family: {OPERATION_BY_FAMILY[r.family]}. "
            f"Current contract: {contract} "
            f"Current request: {json.dumps(r.payload,sort_keys=True)}"
        )
        response=self.client.responses.create(
            model=self.model,
            input=prompt,
            text={"format":{
                "type":"json_schema",
                "name":"chapter13_decision",
                "strict":True,
                "schema":{
                    "type":"object",
                    "properties":{
                        "answer":{"type":"boolean"},
                        "operation":{"type":"string","enum":sorted(ALLOWED_OPERATIONS)},
                    },
                    "required":["answer","operation"],
                    "additionalProperties":False,
                },
            }},
        )
        data=json.loads(response.output_text)
        usage=getattr(response,"usage",None)
        inp=int(getattr(usage,"input_tokens",0) or 0)
        out=int(getattr(usage,"output_tokens",0) or 0)
        return ProviderResult(Answer(data["answer"]),data["operation"],Usage(inp,out))

def make_provider(name:str):
    if name=="mock": return MockProvider()
    if name=="openai": return OpenAIProvider()
    raise ValueError(f"unknown provider: {name}")
