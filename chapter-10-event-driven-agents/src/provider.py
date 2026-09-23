from __future__ import annotations
import json, os, re, time
from abc import ABC, abstractmethod
from .models import Observation, Decision, ProviderUsage
from .ground_truth import authoritative_decision
from .contracts import public_contract

class ReasoningProvider(ABC):
    name: str
    model: str
    @abstractmethod
    def decide(self, obs: Observation, task: str) -> tuple[Decision,ProviderUsage]: ...

class MockProvider(ReasoningProvider):
    name="mock"
    model="deterministic-ground-truth-adapter"
    def decide(self, obs: Observation, task: str):
        return authoritative_decision(obs), ProviderUsage(latency_ms=0.0)

def semantic_label_from_note(note: str) -> str:
    m=re.search(r"\bnote\s+(\d+)\b",note,flags=re.IGNORECASE)
    if not m: raise ValueError(f"Unrecognized synthetic reasoning note: {note!r}")
    labels=("weather","customs","damage","policy_exception")
    return labels[(int(m.group(1))-1)%4]

def build_provider_payload(obs: Observation, task: str) -> dict:
    # Public operational inputs only. Never expose expected_action/expected_label.
    return {
        "task": task,
        "monitor_contract": public_contract(obs.family, obs.contract_version),
        "state": obs.state,
        "previous_state": obs.previous_state,
        "reasoning_required": obs.reasoning_required,
    }

def _parse_json_object(text: str) -> dict:
    text=text.strip()
    if text.startswith("```"):
        text=re.sub(r"^```(?:json)?\s*","",text,flags=re.IGNORECASE)
        text=re.sub(r"\s*```$","",text).strip()
    try:
        data=json.loads(text)
    except json.JSONDecodeError:
        start=text.find("{")
        end=text.rfind("}")
        if start < 0 or end <= start:
            raise
        data=json.loads(text[start:end+1])
    if not isinstance(data,dict):
        raise ValueError("Provider response must be a JSON object.")
    return data

class OpenAIProvider(ReasoningProvider):
    name="openai"
    def __init__(self, model: str | None=None):
        from openai import OpenAI
        self.client=OpenAI()
        self.model=model or os.getenv("CH10_MODEL","gpt-5-mini")

    def decide(self, obs: Observation, task: str):
        payload=build_provider_payload(obs,task)
        prompt=(
            "You are the reasoning component of a controlled event-monitoring benchmark. "
            "Use ONLY the supplied public monitoring contract and observation. "
            "The monitor_contract.trigger_predicate is authoritative. Apply its operator literally; "
            "do not substitute general business intuition for the frozen benchmark rule. "
            "Return exactly one JSON object with keys action, label, explanation. "
            "action must be one of no_action, deterministic_action, reasoning_action. "
            "For reasoning_required=false: evaluate trigger_predicate. If false return no_action; "
            "if true return deterministic_action; label must be null. "
            "For reasoning_required=true: return reasoning_action and classify "
            "'synthetic operational note N' using the PUBLIC frozen taxonomy "
            "((N-1) mod 4) -> [weather, customs, damage, policy_exception]. "
            "Examples: note 1=weather, note 2=customs, note 3=damage, "
            "note 4=policy_exception, note 5=weather. "
            "Do not return relearn; relearning is a routing decision made outside the model. "
            "INPUT="+json.dumps(payload,sort_keys=True,separators=(",",":"))
        )
        t=time.perf_counter()
        r=self.client.responses.create(model=self.model,input=prompt)
        latency=(time.perf_counter()-t)*1000
        data=_parse_json_object(getattr(r,"output_text",""))

        action=data.get("action")
        if action not in {"no_action","deterministic_action","reasoning_action"}:
            raise ValueError(f"Provider returned invalid action: {action!r}")

        label=data.get("label")
        if obs.reasoning_required:
            if action!="reasoning_action":
                raise ValueError(f"Reasoning-required observation returned {action!r}.")
            if label not in {"weather","customs","damage","policy_exception"}:
                raise ValueError(f"Provider returned invalid reasoning label: {label!r}")
        else:
            if action=="reasoning_action":
                raise ValueError("Non-reasoning observation returned reasoning_action.")
            if label is not None:
                raise ValueError(f"Non-reasoning observation returned unexpected label: {label!r}")

        usage=getattr(r,"usage",None)
        inp=int(getattr(usage,"input_tokens",0) or 0)
        out=int(getattr(usage,"output_tokens",0) or 0)
        in_rate=float(os.getenv("CH10_INPUT_USD_PER_MILLION","0"))
        out_rate=float(os.getenv("CH10_OUTPUT_USD_PER_MILLION","0"))
        cost=(inp*in_rate+out*out_rate)/1_000_000
        return Decision(action,label,data.get("explanation","")), ProviderUsage(inp,out,cost,latency)

def build_provider() -> ReasoningProvider:
    p=os.getenv("CH10_PROVIDER","mock").lower()
    if p=="mock": return MockProvider()
    if p=="openai": return OpenAIProvider()
    raise ValueError(f"Unsupported CH10_PROVIDER={p!r}")
