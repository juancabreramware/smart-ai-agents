from types import SimpleNamespace
from src.provider import OpenAIProvider
from src.workload import build_workload
from src.contracts import public_contract

class FakeCompletions:
    def create(self, **kwargs):
        assert "temperature" not in kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(
                content='{"answer":true,"operation":"inventory_reorder"}'
            ))],
            usage=SimpleNamespace(prompt_tokens=11,completion_tokens=7)
        )
class FakeClient:
    def __init__(self):
        self.chat=SimpleNamespace(completions=FakeCompletions())

def test_openai_provider_does_not_send_temperature():
    req=build_workload(1)[0]
    p=OpenAIProvider(FakeClient())
    r=p.reason(req,public_contract(req.family,req.contract_version))
    assert r["status"]=="success"
    assert r["usage"].total_tokens==18
    assert r["error_type"] is None

class FailingCompletions:
    def create(self, **kwargs):
        raise ValueError("diagnostic failure")
class FailingClient:
    def __init__(self):
        self.chat=SimpleNamespace(completions=FailingCompletions())

def test_provider_preserves_sanitized_failure():
    req=build_workload(1)[0]
    p=OpenAIProvider(FailingClient())
    r=p.reason(req,public_contract(req.family,req.contract_version))
    assert r["status"]=="failed"
    assert r["error_type"]=="ValueError"
    assert "diagnostic failure" in r["error_message"]
