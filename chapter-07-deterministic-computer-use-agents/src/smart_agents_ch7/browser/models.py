from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Literal

ActionKind = Literal["goto", "fill", "select", "check", "click", "extract"]


@dataclass(slots=True)
class BrowserAction:
    kind: ActionKind
    target: str | None = None
    value: str | None = None
    key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BrowserAction":
        return cls(
            kind=data["kind"],
            target=data.get("target"),
            value=data.get("value"),
            key=data.get("key"),
        )


@dataclass(slots=True)
class BrowserPlan:
    operation_family: str
    start_path: str
    actions: list[BrowserAction]
    required_args: list[str]
    postcondition: str
    reusable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_family": self.operation_family,
            "start_path": self.start_path,
            "actions": [a.to_dict() for a in self.actions],
            "required_args": list(self.required_args),
            "postcondition": self.postcondition,
            "reusable": self.reusable,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BrowserPlan":
        return cls(
            operation_family=data["operation_family"],
            start_path=data["start_path"],
            actions=[BrowserAction.from_dict(x) for x in data["actions"]],
            required_args=list(data.get("required_args", [])),
            postcondition=data.get("postcondition", ""),
            reusable=bool(data.get("reusable", True)),
        )


@dataclass(slots=True)
class BrowserExecution:
    ok: bool
    extracted: dict[str, str] = field(default_factory=dict)
    action_count: int = 0
    error: str | None = None
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
