from __future__ import annotations
from dataclasses import dataclass
from workflows.schema import WorkflowPlan, ALLOWED_OPS
from workflows.ground_truth import canonical_plan, expected_ops


@dataclass
class ValidationResult:
    ok: bool
    reasons: list[str]


def validate_plan(plan: WorkflowPlan, req: dict, policy: dict) -> ValidationResult:
    reasons = []

    if plan.workflow_family != req["workflow_family"]:
        reasons.append("workflow_family_mismatch")

    unknown = [s.op for s in plan.steps if s.op not in ALLOWED_OPS]
    if unknown:
        reasons.append("unknown_operations")

    actual = [s.op for s in plan.steps]
    expected = expected_ops(req, policy)

    if actual != expected:
        reasons.append("step_sequence_mismatch")

    # Validate the arguments for every expected step against the frozen,
    # deterministic workflow definition. This prevents structurally valid
    # LLM output from reaching the executor with missing or incorrect
    # arguments such as repository, group, project, date, template, or email.
    expected_plan = canonical_plan(req, policy)

    if len(plan.steps) != len(expected_plan.steps):
        reasons.append("step_count_mismatch")
    else:
        for index, (actual_step, expected_step) in enumerate(
            zip(plan.steps, expected_plan.steps)
        ):
            # If operations differ, the sequence check above already records
            # the mismatch. Do not compare arguments across different ops.
            if actual_step.op != expected_step.op:
                continue

            for key, expected_value in expected_step.args.items():
                actual_value = actual_step.args.get(key)

                if actual_value != expected_value:
                    reasons.append(
                        f"step_{index}_{actual_step.op}_arg_{key}_mismatch"
                    )

    if req.get("employment_type") == "contractor":
        # Contractor onboarding must be time bounded.
        if (
            req["workflow_family"] == "engineering_contractor_onboarding"
            and "set_access_expiration" not in actual
        ):
            reasons.append("contractor_missing_expiration")

    return ValidationResult(not reasons, reasons)


def validate_final_state(env, req: dict, policy: dict) -> ValidationResult:
    s = env.person(req["employee_id"])
    f = req["workflow_family"]
    reasons = []

    if f.endswith("onboarding"):
        if not s.identity:
            reasons.append("identity_missing")
        if not s.mailbox:
            reasons.append("mailbox_missing")

    if f.startswith("engineering_"):
        if f.endswith("onboarding") and "engineering" in f:
            if not s.source_control:
                reasons.append("source_control_missing")
            if policy["version"] >= 2 and not s.mfa:
                reasons.append("mfa_missing")

    if (
        f == "finance_employee_onboarding"
        and policy["version"] >= 2
        and not s.security_awareness
    ):
        reasons.append("security_awareness_missing")

    if "offboarding" in f or f == "contractor_expiration":
        if s.identity or not s.disabled:
            reasons.append("identity_not_disabled")

    return ValidationResult(not reasons, reasons)
