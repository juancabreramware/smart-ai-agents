from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any

from smart_agents_ch7.browser.models import BrowserExecution
from smart_agents_ch7.planner.models import TokenUsage
from smart_agents_ch7.validation.ground_truth import AuditResult


@dataclass(slots=True)
class AgentOutcome:
    architecture: str
    request_id: str
    routing_path: str
    llm_called: bool
    planner_model: str | None
    token_usage: TokenUsage
    measured_llm_cost: float
    execution: BrowserExecution
    audit: AuditResult
    capability_id: str | None = None
    capability_version: int | None = None
    compatibility_checks: dict[str, Any] = field(default_factory=dict)
    stale_reuse: bool = False
    invalidated: bool = False
    promoted: bool = False
    raw_response_id: str | None = None
    planner_latency_ms: float = 0.0
    end_to_end_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["token_usage"] = self.token_usage.to_dict()
        d["execution"] = self.execution.to_dict()
        d["audit"] = self.audit.to_dict()
        return d
