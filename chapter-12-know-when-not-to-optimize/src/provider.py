from __future__ import annotations

import json
import os
import urllib.request

from .models import Request, Answer, Usage
from .cost_model import provider_cost_micro
from .contracts import public_operational_contract


class MockProvider:
    model = "deterministic-mock"

    def reason(self, r: Request) -> tuple[Answer, Usage]:
        # Mock is intentionally deterministic and is used only for harness /
        # regression testing. Import locally so the real-provider path has no
        # dependency on the hidden scoring oracle.
        from .scoring import ground_truth

        return (
            ground_truth(r),
            Usage(650, 180, provider_cost_micro(650, 180)),
        )


class OpenAIProvider:
    """
    Minimal Responses API client using only the Python standard library.

    IMPORTANT:
    The real provider receives the public operational contract applicable to
    the current request. It never receives hidden ground truth, future workload
    information, future drift information, or optimizer state.
    """

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("CH12_MODEL", "gpt-5-mini")
        self.key = os.environ["OPENAI_API_KEY"]
        self.url = os.getenv(
            "OPENAI_RESPONSES_URL",
            "https://api.openai.com/v1/responses",
        )

    def reason(self, r: Request) -> tuple[Answer, Usage]:
        schema = {
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "value": {
                    "anyOf": [
                        {"type": "boolean"},
                        {"type": "integer"},
                        {"type": "number"},
                        {"type": "string"},
                    ]
                },
            },
            "required": ["action", "value"],
            "additionalProperties": False,
        }

        contract = public_operational_contract(r.family, r.version)

        prompt = (
            "You are solving one synthetic HarborPoint operational request.\n\n"
            "Apply the following current operational contract exactly:\n\n"
            f"{contract}\n\n"
            "Return only the operational result required by that contract.\n"
            "The JSON field 'action' must use exactly the action name specified "
            "by the contract.\n"
            "The JSON field 'value' must use exactly the value type and meaning "
            "specified by the contract.\n\n"
            "Current request:\n"
            + json.dumps(r.public_dict(), sort_keys=True)
        )

        body = {
            "model": self.model,
            "input": prompt,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "chapter12_answer",
                    "strict": True,
                    "schema": schema,
                }
            },
        }

        req = urllib.request.Request(
            self.url,
            data=json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.load(resp)

        if data.get("status") != "completed":
            raise RuntimeError(
                f"OpenAI response status={data.get('status')}"
            )

        txt = data.get("output_text")

        if not txt:
            # Raw REST Responses payload may not expose the SDK convenience
            # output_text field.
            parts = []
            for item in data.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        parts.append(content.get("text", ""))
            txt = "".join(parts)

        if not txt:
            raise RuntimeError("OpenAI response contained no output_text")

        obj = json.loads(txt)

        if set(obj) != {"action", "value"}:
            raise ValueError("Provider returned unexpected keys")

        usage = data.get("usage", {})
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))

        return (
            Answer(str(obj["action"]), obj["value"]),
            Usage(
                input_tokens,
                output_tokens,
                provider_cost_micro(input_tokens, output_tokens),
            ),
        )


def make_provider(name: str):
    if name == "mock":
        return MockProvider()

    if name == "openai":
        return OpenAIProvider()

    raise ValueError("CH12_PROVIDER must be mock or openai")
