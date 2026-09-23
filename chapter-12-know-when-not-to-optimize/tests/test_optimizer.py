from src.models import OptimizationCase
from src.optimizer import decide
def test_ambiguous_is_reason_only():
    c=OptimizationCase("ambiguous_judgment",observed_count=20,eligible_reuse_count=20,reasoning_cost_estimate_micro=1200)
    assert decide(c,"ambiguous_judgment").decision=="REASON_ONLY"
def test_low_evidence_defers():
    c=OptimizationCase("stable_recurring",observed_count=2,eligible_reuse_count=2,reasoning_cost_estimate_micro=1200)
    assert decide(c,"stable_recurring").decision=="DEFER"
def test_economic_case_promotes():
    c=OptimizationCase("stable_recurring",observed_count=8,eligible_reuse_count=8,reasoning_cost_estimate_micro=1200)
    assert decide(c,"stable_recurring").decision=="PROMOTE"
def test_no_future_fields_in_case():
    c=OptimizationCase("stable_recurring")
    assert not hasattr(c,"future_schedule") and not hasattr(c,"true_remaining_count")
