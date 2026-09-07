"""Learn Once, Execute Many implementation for Chapter 3.

This class is the runnable version of the Chapter 2 architecture:

unknown -> reason -> validate -> capture -> promote
known   -> execute -> validate -> result
failed  -> relearn -> validate -> promote new version
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from .common import fetch_for_model, load_prompt, resolve_source
from .extractor import DeterministicPricingExtractor
from .model_provider import ModelProvider
from .models import (
    Architecture,
    CapabilityRecord,
    ExecutionLedgerEntry,
    ExecutionPath,
    LearnedCapabilityCandidate,
    ModelUsage,
    PricingResult,
    TaskDescriptor,
    ToolUsage,
    utc_now_iso,
)
from .normalizer import normalize_pricing_result
from .registry import CapabilityRegistry
from .telemetry import new_execution_id
from .validator import PricingValidator


class SmartPricingAgent:
    def __init__(self, provider: ModelProvider, registry: CapabilityRegistry | None = None) -> None:
        self.provider = provider
        self.registry = registry or CapabilityRegistry()
        self.extractor = DeterministicPricingExtractor()
        self.validator = PricingValidator()

    def run(self, *, task: TaskDescriptor, experiment_id: str, phase: str, ground_truth_path: Path | None = None) -> tuple[PricingResult, ExecutionLedgerEntry]:
        execution_id, started_iso = new_execution_id(), utc_now_iso()
        started = time.perf_counter()
        model_usage, tool_usage = ModelUsage(), ToolUsage()
        notes: list[str] = []
        fallback = False
        fallback_reason: str | None = None
        capability = self.registry.latest_active(task.vendor_id)
        path = ExecutionPath.DETERMINISTIC if capability else ExecutionPath.REASONING

        try:
            if capability:
                # KNOWN PATH ---------------------------------------------------------
                # First use software. Do not wake the model simply because an LLM is
                # available and feeling chatty.
                page, t = fetch_for_model(capability.source_url, capability.recipe.fetch_mode)
                tool_usage.add(t)
                result = self.extractor.execute(
                    html=page.html,
                    recipe=capability.recipe,
                    vendor_name=task.vendor_name,
                    source_url=page.url,
                )
                validation = self._validate(result, ground_truth_path)
                if validation.passed:
                    self.registry.mark_success(capability)
                    return result, self._ledger(
                        experiment_id, execution_id, phase, task, path, capability,
                        started_iso, started, model_usage, tool_usage,
                        True, validation.score, fallback, fallback_reason, notes,
                    )

                # Validation says our memory no longer deserves trust. Preserve the
                # failed version for audit, mark it degraded, and let intelligence back in.
                fallback = True
                fallback_reason = "; ".join(i.code for i in validation.issues) or "VALIDATION_FAILED"
                notes.append("Stored capability failed validation; entering relearning path.")
                notes.extend(i.message for i in validation.issues[:10])
                self.registry.mark_failure(capability)
                path = ExecutionPath.RELEARNING

                candidate, m = self._learn_or_repair(
                    task=task,
                    source_url=page.url,
                    page_html=page.html,
                    page_text=page.visible_text,
                    previous_capability=capability,
                    failure_details=fallback_reason,
                    repair=True,
                )
                model_usage.add(m)
                capability, result, promotion_notes = self._promote_candidate(
                    task=task,
                    candidate=candidate,
                    page_html=page.html,
                    source_url=page.url,
                    ground_truth_path=ground_truth_path,
                    parent_version=capability.version,
                )
                notes.extend(promotion_notes)
                validation = self._validate(result, ground_truth_path)
                return result, self._ledger(
                    experiment_id, execution_id, phase, task, path, capability,
                    started_iso, started, model_usage, tool_usage,
                    validation.passed, validation.score, fallback, fallback_reason, notes,
                )

            # UNKNOWN PATH -----------------------------------------------------------
            source_url, m, t = resolve_source(task, self.provider)
            model_usage.add(m); tool_usage.add(t)
            page, t = fetch_for_model(source_url, "auto")
            tool_usage.add(t)
            candidate, m = self._learn_or_repair(
                task=task,
                source_url=page.url,
                page_html=page.html,
                page_text=page.visible_text,
                previous_capability=None,
                failure_details=None,
                repair=False,
            )
            model_usage.add(m)
            capability, result, promotion_notes = self._promote_candidate(
                task=task,
                candidate=candidate,
                page_html=page.html,
                source_url=page.url,
                ground_truth_path=ground_truth_path,
                parent_version=None,
            )
            notes.extend(promotion_notes)
            validation = self._validate(result, ground_truth_path)
            return result, self._ledger(
                experiment_id, execution_id, phase, task, path, capability,
                started_iso, started, model_usage, tool_usage,
                validation.passed, validation.score, fallback, fallback_reason, notes,
            )

        except Exception as exc:
            notes.append(f"ERROR: {type(exc).__name__}: {exc}")
            empty = PricingResult(
                vendor=task.vendor_name,
                retrieved_at=utc_now_iso(),
                plans=[],
                source_url=capability.source_url if capability else (task.pricing_url or ""),
            )
            return empty, self._ledger(
                experiment_id, execution_id, phase, task, path, capability,
                started_iso, started, model_usage, tool_usage,
                False, 0.0, fallback, fallback_reason, notes,
            )

    def _learn_or_repair(self, *, task: TaskDescriptor, source_url: str, page_html: str, page_text: str, previous_capability: CapabilityRecord | None, failure_details: str | None, repair: bool) -> tuple[LearnedCapabilityCandidate, ModelUsage]:
        payload: dict = {
            "vendor_name": task.vendor_name,
            "source_url": source_url,
            "visible_text": page_text,
            "html": page_html,
        }
        if repair and previous_capability:
            payload["previous_recipe"] = previous_capability.recipe.model_dump()
            payload["validation_failure"] = failure_details
        return self.provider.structured(
            instructions=load_prompt("repair-v1.txt" if repair else "discovery-v1.txt"),
            input_text=json.dumps(payload, ensure_ascii=False),
            response_model=LearnedCapabilityCandidate,
            schema_name="chapter3_capability_candidate",
        )

    def _promote_candidate(self, *, task: TaskDescriptor, candidate: LearnedCapabilityCandidate, page_html: str, source_url: str, ground_truth_path: Path | None, parent_version: int | None) -> tuple[CapabilityRecord, PricingResult, list[str]]:
        notes: list[str] = []

        # PROMOTION GATE 1: the model's direct answer must itself be correct enough.
        # Normalize first using the same trusted layer applied to deterministic output.
        # The LLM may say "per month" while our canonical contract says "month"; that is
        # a stable formatting rule, not a reason to discard an otherwise correct capability.
        candidate.result = normalize_pricing_result(candidate.result)
        direct_validation = self._validate(candidate.result, ground_truth_path)
        if not direct_validation.passed:
            raise RuntimeError(
                "Candidate direct extraction failed validation: "
                + "; ".join(i.message for i in direct_validation.issues)
            )

        # PROMOTION GATE 2: the artifact must independently reproduce the result with
        # ZERO additional model inference. Otherwise we learned a story, not a capability.
        deterministic_result = self.extractor.execute(
            html=page_html,
            recipe=candidate.recipe,
            vendor_name=task.vendor_name,
            source_url=source_url,
        )
        recipe_validation = self._validate(deterministic_result, ground_truth_path)
        if not recipe_validation.passed:
            raise RuntimeError(
                "Generated recipe failed promotion validation: "
                + "; ".join(i.message for i in recipe_validation.issues)
            )

        # PROMOTION GATE 3: normalized values must match the model's direct result.
        if self._canonical(candidate.result) != self._canonical(deterministic_result):
            raise RuntimeError("Generated recipe did not reproduce the model's normalized extraction; artifact rejected.")

        record = self.registry.create_or_upgrade(
            vendor_id=task.vendor_id,
            source_url=source_url,
            recipe=candidate.recipe,
            task_signature={
                "task_type": task.task_type,
                "vendor_id": task.vendor_id,
                "domain": task.domain,
            },
            parent_version=parent_version,
        )
        self.registry.mark_success(record)
        notes.append(f"Promoted {record.capability_id} version {record.version}.")
        return record, deterministic_result, notes

    @staticmethod
    def _canonical(result: PricingResult) -> list[tuple]:
        return sorted((p.plan_name, p.displayed_price, p.currency, p.billing_period, p.usage_limit) for p in result.plans)

    def _validate(self, result: PricingResult, ground_truth_path: Path | None):
        structural = self.validator.validate_structural(result)
        if not structural.passed or ground_truth_path is None:
            return structural
        return self.validator.validate_against_ground_truth(result, ground_truth_path)

    @staticmethod
    def _ledger(experiment_id, execution_id, phase, task, path, capability, started_iso, started, model_usage, tool_usage, passed, score, fallback, fallback_reason, notes):
        return ExecutionLedgerEntry(
            experiment_id=experiment_id,
            execution_id=execution_id,
            architecture=Architecture.SMART,
            phase=phase,
            task_type=task.task_type,
            vendor_id=task.vendor_id,
            path=path,
            capability_id=capability.capability_id if capability else None,
            capability_version=capability.version if capability else None,
            started_at=started_iso,
            finished_at=utc_now_iso(),
            latency_ms=(time.perf_counter() - started) * 1000,
            model=model_usage,
            tools=tool_usage,
            total_cost_usd=model_usage.cost_usd + tool_usage.cost_usd,
            validation_passed=passed,
            correctness_score=score,
            fallback_occurred=fallback,
            fallback_reason=fallback_reason,
            result="SUCCESS" if passed else "FAILURE",
            notes=notes,
        )
