from __future__ import annotations

import json
import os
import urllib.request
import time
from typing import Any

from smart_agents_ch7.benchmark.models import BenchmarkRequest
from smart_agents_ch7.browser.models import BrowserPlan
from smart_agents_ch7.portal.contracts import UIContract
from .models import PlannerResult, TokenUsage


PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["operation_family", "start_path", "actions", "required_args", "postcondition", "reusable"],
    "properties": {
        "operation_family": {"type": "string"},
        "start_path": {"type": "string"},
        "actions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["kind", "target", "value", "key"],
                "properties": {
                    "kind": {"type": "string", "enum": ["goto", "fill", "select", "check", "click", "extract"]},
                    "target": {"type": ["string", "null"]},
                    "value": {"type": ["string", "null"]},
                    "key": {"type": ["string", "null"]},
                },
            },
        },
        "required_args": {"type": "array", "items": {"type": "string"}},
        "postcondition": {"type": "string"},
        "reusable": {"type": "boolean"},
    },
}


class OpenAIPlanner:
    """GPT-5.6 Sol planner using the Responses API and Structured Outputs.

    The real benchmark should pin model/pricing in the experiment manifest before execution.
    The planner emits parameterized browser actions: request-specific values must use
    {{argument_name}} placeholders so a validated plan can become a reusable capability.
    """

    def __init__(self, model: str | None = None, reasoning_effort: str | None = None, timeout_seconds: int = 120):
        self.model = model or os.getenv("CH7_MODEL", "gpt-5.6-sol")
        self.reasoning_effort = reasoning_effort or os.getenv("CH7_REASONING_EFFORT", "medium")
        self.timeout_seconds = timeout_seconds
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for --planner openai")

    def plan(self, request: BenchmarkRequest, contract: UIContract) -> PlannerResult:
        system = (
            "You are the planning component of a controlled browser-automation benchmark. "
            "Return only the structured BrowserPlan required by the schema. Use only selectors and routes "
            "present in the supplied UI contract. Use {{argument_name}} placeholders for all request-specific "
            "values. Do not invent controls. The plan must accomplish the business request and be suitable for "
            "deterministic execution. Set reusable=false when reasoning_required is true."
        )
        user = json.dumps({
            "business_request": request.to_dict(),
            "ui_contract": contract.to_dict(),
        }, sort_keys=True)
        payload = {
            "model": self.model,
            "reasoning": {"effort": self.reasoning_effort},
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": system}]},
                {"role": "user", "content": [{"type": "input_text", "text": user}]},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "chapter7_browser_plan",
                    "schema": PLAN_SCHEMA,
                    "strict": True,
                }
            },
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        started = time.perf_counter()
        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        elapsed_ms = (time.perf_counter() - started) * 1000

        text = self._extract_output_text(data)
        plan = BrowserPlan.from_dict(json.loads(text))
        usage_raw = data.get("usage") or {}
        input_details = usage_raw.get("input_tokens_details") or {}
        output_details = usage_raw.get("output_tokens_details") or {}
        usage = TokenUsage(
            input_tokens=int(usage_raw.get("input_tokens") or 0),
            cached_input_tokens=int(input_details.get("cached_tokens") or 0),
            output_tokens=int(usage_raw.get("output_tokens") or 0),
            reasoning_tokens=int(output_details.get("reasoning_tokens") or 0),
        )
        return PlannerResult(plan=plan, usage=usage, model=self.model, raw_response_id=data.get("id"), elapsed_ms=elapsed_ms)

    @staticmethod
    def _extract_output_text(data: dict[str, Any]) -> str:
        # Responses API returns assistant content inside output[] messages.
        for item in data.get("output") or []:
            if item.get("type") != "message":
                continue
            for content in item.get("content") or []:
                if content.get("type") == "output_text" and content.get("text"):
                    return content["text"]
        # Some SDK/proxy responses expose a convenience output_text field.
        if isinstance(data.get("output_text"), str):
            return data["output_text"]
        raise RuntimeError("Responses API did not return output_text")
