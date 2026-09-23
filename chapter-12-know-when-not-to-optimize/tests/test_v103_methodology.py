from src.models import OptimizationCase,Request
from src.optimizer import decide,_future_reuse_estimate,FORWARD_OPERATING_HORIZON_REQUESTS
from src.capabilities import promote,execute

def test_declared_forward_horizon_is_180():assert FORWARD_OPERATING_HORIZON_REQUESTS==180
def test_conservative_recurrence_discount_small_sample():
    c=OptimizationCase("stable_rare",observed_count=4,eligible_reuse_count=4,reasoning_cost_estimate_micro=1200)
    assert _future_reuse_estimate(c,11)<65
def test_ambiguous_is_reason_only():
    c=OptimizationCase("ambiguous_judgment",observed_count=30,eligible_reuse_count=30,reasoning_cost_estimate_micro=1200);assert decide(c,"ambiguous_judgment",180).decision=="REASON_ONLY"
def test_capability_runtime_is_independent_and_correct_for_known_operation():
    r=Request("x",1,"stable_recurring",1,{"on_hand":2,"reserved":1,"reorder_point":5});cap=promote(r,"test");a=execute(cap,r);assert a.action=="reorder" and a.value is True
