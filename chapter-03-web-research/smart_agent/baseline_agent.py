"""Reasoning-First baseline.

It is intentionally competent. The baseline gets the same model, source, HTML and output
schema as the Smart Agent. The controlled difference is cross-run procedural memory.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from .common import fetch_for_model, load_prompt, resolve_source
from .model_provider import ModelProvider
from .models import (
    Architecture, ExecutionLedgerEntry, ExecutionPath, ModelUsage,
    PricingResult, TaskDescriptor, ToolUsage, utc_now_iso,
)
from .normalizer import normalize_pricing_result
from .telemetry import new_execution_id
from .validator import PricingValidator


class BaselineAgent:
    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider
        self.validator = PricingValidator()

    def run(self, *, task: TaskDescriptor, experiment_id: str, phase: str, ground_truth_path: Path | None = None) -> tuple[PricingResult, ExecutionLedgerEntry]:
        execution_id, started_iso = new_execution_id(), utc_now_iso()
        started = time.perf_counter()
        model_usage, tool_usage = ModelUsage(), ToolUsage()
        notes: list[str] = []
        try:
            source_url, m, t = resolve_source(task, self.provider)
            model_usage.add(m); tool_usage.add(t)
            page, t = fetch_for_model(source_url, "auto")
            tool_usage.add(t)
            result, m = self.provider.structured(
                instructions=load_prompt("baseline-research-v1.txt"),
                input_text=json.dumps({
                    "vendor_name": task.vendor_name,
                    "source_url": page.url,
                    "visible_text": page.visible_text,
                    "html": page.html,
                }, ensure_ascii=False),
                response_model=PricingResult,
                schema_name="chapter3_pricing_result",
            )
            model_usage.add(m)

            # The model is responsible for understanding the page; deterministic software
            # is responsible for stable representation rules such as "per month" -> "month".
            # The Smart Agent uses this exact same normalizer, preserving benchmark fairness.
            result = normalize_pricing_result(result)
            validation = self.validator.validate_structural(result)
            if ground_truth_path and validation.passed:
                validation = self.validator.validate_against_ground_truth(result, ground_truth_path)
            notes.extend(i.message for i in validation.issues)
            return result, self._ledger(
                experiment_id, execution_id, phase, task, started_iso, started,
                model_usage, tool_usage, validation.passed, validation.score, notes
            )
        except Exception as exc:
            notes.append(f"ERROR: {type(exc).__name__}: {exc}")
            result = PricingResult(vendor=task.vendor_name, retrieved_at=utc_now_iso(), plans=[], source_url=task.pricing_url or "")
            return result, self._ledger(
                experiment_id, execution_id, phase, task, started_iso, started,
                model_usage, tool_usage, False, 0.0, notes
            )

    def _ledger(self, experiment_id, execution_id, phase, task, started_iso, started, model_usage, tool_usage, passed, score, notes):
        return ExecutionLedgerEntry(
            experiment_id=experiment_id,
            execution_id=execution_id,
            architecture=Architecture.BASELINE,
            phase=phase,
            task_type=task.task_type,
            vendor_id=task.vendor_id,
            path=ExecutionPath.REASONING,
            started_at=started_iso,
            finished_at=utc_now_iso(),
            latency_ms=(time.perf_counter() - started) * 1000,
            model=model_usage,
            tools=tool_usage,
            total_cost_usd=model_usage.cost_usd + tool_usage.cost_usd,
            validation_passed=passed,
            correctness_score=score,
            result="SUCCESS" if passed else "FAILURE",
            notes=notes,
        )
