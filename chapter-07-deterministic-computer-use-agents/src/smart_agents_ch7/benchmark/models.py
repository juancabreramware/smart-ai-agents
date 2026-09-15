from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Literal

Phase = Literal["A", "B", "C"]
UIVersion = Literal["V1", "V2"]


@dataclass(slots=True)
class BenchmarkRequest:
    request_id: str
    phase: Phase
    ui_version: UIVersion
    operation_family: str
    args: dict[str, Any]
    reasoning_required: bool = False
    v2_affected: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BenchmarkRequest":
        return cls(**data)
