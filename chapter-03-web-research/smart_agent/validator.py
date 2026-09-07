"""Validation is the guardrail that makes deterministic reuse credible."""

from __future__ import annotations

import json
from pathlib import Path

from .models import PricingResult, ValidationIssue, ValidationResult


class PricingValidator:
    def validate_structural(self, result: PricingResult) -> ValidationResult:
        issues: list[ValidationIssue] = []
        if not result.plans:
            issues.append(ValidationIssue(code="NO_PLANS", message="No plans were extracted."))
        for i, plan in enumerate(result.plans):
            if not plan.plan_name.strip():
                issues.append(ValidationIssue(code="EMPTY_PLAN_NAME", message=f"Plan {i} has no name."))
            if plan.displayed_price is not None and plan.displayed_price < 0:
                issues.append(ValidationIssue(code="NEGATIVE_PRICE", message=f"Plan {i} has negative price."))
        return ValidationResult(passed=not issues, score=1.0 if not issues else 0.0, issues=issues)

    def validate_against_ground_truth(self, result: PricingResult, ground_truth_path: Path) -> ValidationResult:
        expected = json.loads(ground_truth_path.read_text(encoding="utf-8"))
        exp = {p["plan_name"]: p for p in expected["plans"]}
        act = {p.plan_name: p for p in result.plans}
        issues: list[ValidationIssue] = []
        checks = passed = 0

        for name, e in exp.items():
            checks += 1
            if name not in act:
                issues.append(ValidationIssue(code="MISSING_PLAN", message=f"Missing plan {name!r}."))
                continue
            passed += 1
            a = act[name]
            for field in ["displayed_price", "currency", "billing_period", "usage_limit"]:
                checks += 1
                if getattr(a, field) == e.get(field):
                    passed += 1
                else:
                    issues.append(ValidationIssue(
                        code=f"FIELD_MISMATCH_{field.upper()}",
                        message=f"{name}.{field}: expected {e.get(field)!r}, got {getattr(a, field)!r}",
                    ))

        for name in act.keys() - exp.keys():
            checks += 1
            issues.append(ValidationIssue(code="EXTRA_PLAN", message=f"Unexpected plan {name!r}."))

        score = passed / checks if checks else 0.0
        return ValidationResult(passed=(score == 1.0), score=score, issues=issues)
