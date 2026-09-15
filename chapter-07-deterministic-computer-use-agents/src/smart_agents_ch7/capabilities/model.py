from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from smart_agents_ch7.browser.models import BrowserPlan


@dataclass(slots=True)
class UICapability:
    capability_id: str
    operation_family: str
    capability_version: int
    ui_contract_version: str
    contract_fingerprint: str
    plan: BrowserPlan
    validation_state: str = "VALIDATED"
    reuse_count: int = 0
    failure_count: int = 0
    superseded_by: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["plan"] = self.plan.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UICapability":
        copy = dict(data)
        copy["plan"] = BrowserPlan.from_dict(copy["plan"])
        return cls(**copy)
