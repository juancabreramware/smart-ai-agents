from __future__ import annotations

from dataclasses import dataclass, asdict
import os
from typing import Any

from smart_agents_ch7.planner.models import TokenUsage


@dataclass(frozen=True, slots=True)
class Pricing:
    model: str = "gpt-5.6-sol"
    input_per_million: float = 4.00
    cached_input_per_million: float = 0.40
    output_per_million: float = 20.00
    source_note: str = "Pinned benchmark pricing; verify official pricing immediately before canonical run."

    @classmethod
    def from_env(cls, model: str) -> "Pricing":
        return cls(
            model=model,
            input_per_million=float(os.getenv("CH7_INPUT_PER_MTOK", "4.00")),
            cached_input_per_million=float(os.getenv("CH7_CACHED_INPUT_PER_MTOK", "0.40")),
            output_per_million=float(os.getenv("CH7_OUTPUT_PER_MTOK", "20.00")),
        )

    def cost(self, usage: TokenUsage) -> float:
        # input_tokens includes cached tokens in the provider usage object. Charge the uncached remainder at full rate.
        uncached = max(0, usage.input_tokens - usage.cached_input_tokens)
        return (
            uncached * self.input_per_million
            + usage.cached_input_tokens * self.cached_input_per_million
            + usage.output_tokens * self.output_per_million
        ) / 1_000_000

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
