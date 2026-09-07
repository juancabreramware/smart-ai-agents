"""Canonical data contracts for the Chapter 3 experiment.

This file is intentionally heavily commented. The repository accompanies a technical
book, so the code should explain *why* the contract exists, not merely satisfy Python.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    """Return an explicit UTC timestamp suitable for ledgers and capability metadata."""
    return datetime.now(timezone.utc).isoformat()


class Architecture(str, Enum):
    BASELINE = "BASELINE"
    SMART = "SMART"


class ExecutionPath(str, Enum):
    """The path a particular execution actually took."""
    REASONING = "REASONING"
    DETERMINISTIC = "DETERMINISTIC"
    RELEARNING = "RELEARNING"


class CapabilityStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    EXPIRED = "EXPIRED"
    DISABLED = "DISABLED"


class PricePlan(BaseModel):
    """One normalized pricing plan returned by BOTH architectures."""
    plan_name: str
    displayed_price: float | None = None
    currency: str | None = None
    billing_period: str | None = None
    usage_limit: str | None = None
    notes: str | None = None


class PricingResult(BaseModel):
    """Common output contract. Same schema means a fair comparison."""
    vendor: str
    retrieved_at: str
    plans: list[PricePlan]
    source_url: str


class FieldRule(BaseModel):
    """Constrained extraction instruction for one field inside one plan container.

    The LLM can select CSS and regex, but cannot inject arbitrary Python or shell code.
    That makes the learned artifact inspectable and substantially safer for Chapter 3.
    """
    selector: str | None = None
    attribute: str = "text"
    regex: str | None = None


class ExtractionRecipe(BaseModel):
    """Executable Memory: a learned procedure represented as trusted data."""
    fetch_mode: Literal["requests", "playwright", "auto"] = "auto"
    container_selector: str
    plan_name: FieldRule
    displayed_price: FieldRule
    # Optional separate currency rule supports sites where the amount and currency are
    # rendered in different elements (for example: <span>49</span><span>USD</span>).
    # If omitted, the deterministic normalizer infers currency from displayed_price.
    currency: FieldRule | None = None
    billing_period: FieldRule | None = None
    usage_limit: FieldRule | None = None


class LearnedCapabilityCandidate(BaseModel):
    """Structured output produced during first-time learning or repair."""
    result: PricingResult
    recipe: ExtractionRecipe
    rationale: str = Field(description="Why the selectors represent the page's plan structure.")


class SourceSelection(BaseModel):
    selected_url: str | None
    reason: str


class ValidationIssue(BaseModel):
    code: str
    message: str


class ValidationResult(BaseModel):
    passed: bool
    score: float = 0.0
    issues: list[ValidationIssue] = Field(default_factory=list)


class TaskDescriptor(BaseModel):
    """Structured form of the recurring research request."""
    task_type: str = "saas_pricing_research"
    vendor_id: str
    vendor_name: str
    domain: str
    pricing_url: str | None = None
    search_query: str | None = None


class CapabilityRecord(BaseModel):
    """Human-readable record stored in the file-backed Capability Registry."""
    capability_id: str
    version: int
    status: CapabilityStatus = CapabilityStatus.ACTIVE
    task_signature: dict[str, Any]
    source_url: str
    recipe: ExtractionRecipe
    created_at: str = Field(default_factory=utc_now_iso)
    last_validated_at: str = Field(default_factory=utc_now_iso)
    successes: int = 0
    failures: int = 0
    fallback_count: int = 0
    parent_version: int | None = None


class ModelUsage(BaseModel):
    """Measured model usage for one whole agent execution."""
    calls: int = 0
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    response_ids: list[str] = Field(default_factory=list)

    def add(self, other: "ModelUsage") -> None:
        self.calls += other.calls
        self.input_tokens += other.input_tokens
        self.cached_input_tokens += other.cached_input_tokens
        self.output_tokens += other.output_tokens
        self.cost_usd += other.cost_usd
        self.response_ids.extend(other.response_ids)


class ToolUsage(BaseModel):
    search_calls: int = 0
    browser_calls: int = 0
    http_calls: int = 0
    cost_usd: float = 0.0

    def add(self, other: "ToolUsage") -> None:
        self.search_calls += other.search_calls
        self.browser_calls += other.browser_calls
        self.http_calls += other.http_calls
        self.cost_usd += other.cost_usd


class ExecutionLedgerEntry(BaseModel):
    """One normalized audit/economics record. Chapter 14 will love this file."""
    experiment_id: str
    execution_id: str
    architecture: Architecture
    phase: str
    task_type: str
    vendor_id: str
    path: ExecutionPath
    capability_id: str | None = None
    capability_version: int | None = None
    started_at: str
    finished_at: str
    latency_ms: float
    model: ModelUsage
    tools: ToolUsage
    deterministic_compute_cost_usd: float = 0.0
    validation_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    validation_passed: bool
    correctness_score: float | None = None
    fallback_occurred: bool = False
    fallback_reason: str | None = None
    result: Literal["SUCCESS", "FAILURE"]
    notes: list[str] = Field(default_factory=list)


class ExperimentManifest(BaseModel):
    experiment_id: str
    created_at: str = Field(default_factory=utc_now_iso)
    provider: str
    model_name: str
    git_commit: str | None = None
    python_version: str
    platform: str
    config: dict[str, Any]
    pricing_snapshot: dict[str, float]
