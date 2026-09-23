from src.models import OptimizationCase
from src.optimizer import decide


def test_economic_insufficiency_remains_defer_not_terminal_reason_only():
    c = OptimizationCase(
        "stable_rare",
        observed_count=4,
        eligible_reuse_count=4,
        reasoning_cost_estimate_micro=1200,
    )

    result = decide(c, "stable_rare", 180)

    assert result.decision == "DEFER"
    assert result.decision_reason == "BREAK_EVEN_NOT_YET_CLEARED"
    assert result.expected_reuse_value_micro <= result.expected_optimization_cost_micro


def test_emerging_pattern_can_remain_reevaluable_before_break_even():
    c = OptimizationCase(
        "emerging_pattern",
        observed_count=4,
        eligible_reuse_count=4,
        reasoning_cost_estimate_micro=1200,
    )

    result = decide(c, "emerging_pattern", 180)

    assert result.decision == "DEFER"
    assert result.decision_reason == "BREAK_EVEN_NOT_YET_CLEARED"
    assert result.expected_reuse_value_micro <= result.expected_optimization_cost_micro


def test_economic_case_promotes_only_after_break_even_is_cleared():
    c = OptimizationCase(
        "emerging_pattern",
        observed_count=16,
        eligible_reuse_count=16,
        reasoning_cost_estimate_micro=1200,
    )

    result = decide(c, "emerging_pattern", 120)

    assert result.expected_reuse_value_micro > result.expected_optimization_cost_micro
    assert result.decision == "PROMOTE"
    assert result.decision_reason == "BREAK_EVEN_CLEARED"


def test_ambiguous_work_remains_reason_only():
    c = OptimizationCase(
        "ambiguous_judgment",
        observed_count=30,
        eligible_reuse_count=30,
        reasoning_cost_estimate_micro=1200,
    )

    result = decide(c, "ambiguous_judgment", 180)

    assert result.decision == "REASON_ONLY"
    assert result.decision_reason == "TASK_NOT_SAFELY_REDUCIBLE"


