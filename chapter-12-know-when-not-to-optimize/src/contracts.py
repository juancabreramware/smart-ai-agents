from __future__ import annotations
from dataclasses import dataclass

FAMILIES = (
    "stable_recurring",
    "stable_rare",
    "volatile_recurring",
    "high_validation_recurring",
    "ambiguous_judgment",
    "emerging_pattern",
)

@dataclass(frozen=True)
class FamilyContract:
    family: str
    optimizable: bool
    validation_burden: str
    max_drift_rate_ppm: int

CONTRACTS = {
    "stable_recurring": FamilyContract("stable_recurring", True, "low", 250_000),
    "stable_rare": FamilyContract("stable_rare", True, "low", 250_000),
    "volatile_recurring": FamilyContract("volatile_recurring", True, "medium", 120_000),
    "high_validation_recurring": FamilyContract("high_validation_recurring", True, "high", 250_000),
    "ambiguous_judgment": FamilyContract("ambiguous_judgment", False, "not_applicable", 0),
    "emerging_pattern": FamilyContract("emerging_pattern", True, "low", 250_000),
}

def version_for(family: str, sequence: int) -> int:
    if family == "volatile_recurring":
        if sequence >= 121: return 3
        if sequence >= 91: return 2
    return 1

# ---------------------------------------------------------------------------
# Public operational contracts
# ---------------------------------------------------------------------------
# These rules are information available to an operational reasoning agent.
# They contain no future workload counts, future drift schedule, expected
# benchmark answers, optimizer decisions, or hidden scoring state.
#
# The hidden scoring oracle independently implements the same frozen business
# policy in scoring.py. Providers must reason from these public contracts,
# never by calling scoring.ground_truth().

PUBLIC_OPERATIONAL_CONTRACTS = {
    ("stable_recurring", 1): """
Inventory reorder policy:
- Compute available inventory as on_hand - reserved.
- If available inventory is less than reorder_point:
    action = "reorder"
    value = true
- Otherwise:
    action = "no_action"
    value = false
""".strip(),

    ("stable_rare", 1): """
Invoice escalation policy:
- Escalate only when BOTH conditions are true:
    amount >= 5000
    days_open >= 10
- If both conditions are true:
    action = "escalate"
    value = true
- Otherwise:
    action = "no_action"
    value = false
""".strip(),

    ("volatile_recurring", 1): """
Order-priority policy, version 1:
- Prioritize when age_hours > 48 OR priority is true.
- If prioritized:
    action = "prioritize"
    value = true
- Otherwise:
    action = "no_action"
    value = false
""".strip(),

    ("volatile_recurring", 2): """
Order-priority policy, version 2:
- Prioritize when age_hours > 36 OR priority is true.
- If prioritized:
    action = "prioritize"
    value = true
- Otherwise:
    action = "no_action"
    value = false
""".strip(),

    ("volatile_recurring", 3): """
Order-priority policy, version 3:
- Prioritize when age_hours > 30 OR priority is true.
- If prioritized:
    action = "prioritize"
    value = true
- Otherwise:
    action = "no_action"
    value = false
""".strip(),

    ("high_validation_recurring", 1): """
Supplier review policy:
- Compute score = quality * 0.6 + delivery * 0.4.
- Round score to two decimal places.
- If score < 82:
    action = "review"
- Otherwise:
    action = "approve"
- value must be the numeric score, not a boolean.
""".strip(),

    ("ambiguous_judgment", 1): """
Customer-account review policy:
- Compute adjusted risk as:
    risk
    + 12 when past_due is true
    + 8 when dispute is true
    - 6 when tenure_years >= 5
- If adjusted risk >= 72:
    action = "manual_review"
    value = true
- Otherwise:
    action = "continue"
    value = false
""".strip(),

    ("emerging_pattern", 1): """
Shipment exception policy:
- Expedite when eta_hours > promised_hours + 2.
- If expedited:
    action = "expedite"
    value = true
- Otherwise:
    action = "no_action"
    value = false
""".strip(),
}


def public_operational_contract(family: str, version: int) -> str:
    try:
        return PUBLIC_OPERATIONAL_CONTRACTS[(family, version)]
    except KeyError as exc:
        raise ValueError(
            f"No public operational contract for {family} v{version}"
        ) from exc

PUBLIC_OPERATIONAL_CONTRACT_VERSION = "chapter12-provider-contract-v1.0.4"


def public_operational_contract_manifest() -> dict:
    """
    Canonical semantic representation of the public contracts supplied to the
    real reasoning provider.

    Tuple dictionary keys are converted into explicit family/version records so
    hashing does not depend on Python tuple serialization or source formatting.
    """
    return {
        "version": PUBLIC_OPERATIONAL_CONTRACT_VERSION,
        "contracts": [
            {
                "family": family,
                "version": version,
                "contract": PUBLIC_OPERATIONAL_CONTRACTS[(family, version)],
            }
            for family, version in sorted(PUBLIC_OPERATIONAL_CONTRACTS)
        ],
    }
