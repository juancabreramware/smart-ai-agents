import json
from .models import Usage
from .contracts import ALLOWLIST

class OpenAIProvider:
    model="gpt-5-mini"

    def __init__(self, client=None):
        if client is None:
            from openai import OpenAI
            client=OpenAI()
        self.client=client

    @staticmethod
    def _sanitize_error(exc):
        # Preserve useful diagnostics without serializing request headers, API keys,
        # response bodies, or arbitrary exception internals.
        msg=str(exc).replace("\r"," ").replace("\n"," ").strip()
        if len(msg)>500:
            msg=msg[:497]+"..."
        return type(exc).__name__, msg

    @staticmethod
    def _exception_usage(exc):
        # Most SDK exceptions do not expose token usage. If a compatible usage
        # object is present, preserve it; otherwise explicitly record zero.
        u=getattr(exc,"usage",None)
        if u is None:
            return Usage(0,0)
        inp=getattr(u,"prompt_tokens",getattr(u,"input_tokens",0)) or 0
        out=getattr(u,"completion_tokens",getattr(u,"output_tokens",0)) or 0
        return Usage(int(inp),int(out))

    def reason(self, req, contract, attempt_no=1):
        schema={
            "type":"json_schema",
            "json_schema":{
                "name":"decision",
                "strict":True,
                "schema":{
                    "type":"object",
                    "properties":{
                        "answer":{"type":"boolean"},
                        "operation":{"type":"string","enum":sorted(ALLOWLIST)}
                    },
                    "required":["answer","operation"],
                    "additionalProperties":False
                }
            }
        }
        try:
            resp=self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role":"system",
                        "content":"Apply only the supplied public business contract. Return the boolean decision and allowlisted operation."
                    },
                    {
                        "role":"user",
                        "content":json.dumps({
                            "family":req.family,
                            "contract_version":req.contract_version,
                            "public_contract":contract,
                            "request":req.payload
                        },sort_keys=True)
                    }
                ],
                response_format=schema,
                # IMPORTANT v1.0.1:
                # Do not send temperature=0. The successful Chapter 14 provider
                # diagnostic used GPT-5-mini without a temperature override.
            )
            data=json.loads(resp.choices[0].message.content)
            u=resp.usage
            return {
                "status":"success",
                "usage":Usage(int(u.prompt_tokens),int(u.completion_tokens)),
                "answer":bool(data["answer"]),
                "operation":data["operation"],
                "error_type":None,
                "error_message":None,
            }
        except Exception as exc:
            error_type,error_message=self._sanitize_error(exc)
            return {
                "status":"failed",
                "usage":self._exception_usage(exc),
                "answer":None,
                "operation":contract["operation"],
                "error_type":error_type,
                "error_message":error_message,
            }

def __getattr__(name):
    if name == "MockProvider":
        from .mock_provider import MockProvider
        return MockProvider
    raise AttributeError(name)
