from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from smart_agents_ch7.browser.models import BrowserPlan


@dataclass(slots=True)
class TokenUsage:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PlannerResult:
    plan: BrowserPlan
    usage: TokenUsage
    model: str
    raw_response_id: str | None = None
    elapsed_ms: float = 0.0
