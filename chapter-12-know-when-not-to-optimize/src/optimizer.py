from __future__ import annotations
import math
from .models import OptimizationCase
from .contracts import CONTRACTS
from .cost_model import DEFAULTS

MIN_OBSERVATIONS=4
REEVALUATE_EVERY=2
SAFETY_MARGIN_MICRO=1200
DEFAULT_REASONING_ESTIMATE_MICRO=1100
FORWARD_OPERATING_HORIZON_REQUESTS=180
POLICY_HORIZON_REQUESTS=FORWARD_OPERATING_HORIZON_REQUESTS
# Conservative one-sided recurrence estimate. 2.576 corresponds to a 99% two-sided
# Wilson interval; we use only its lower bound. This discounts small/noisy samples
# without consulting benchmark remainder or future arrivals.
RECURRENCE_WILSON_Z=2.576

def _wilson_lower(successes:int, trials:int, z:float=RECURRENCE_WILSON_Z)->float:
    if trials <= 0 or successes <= 0:
        return 0.0
    successes=min(successes,trials)
    p=successes/trials
    z2=z*z
    den=1.0+z2/trials
    center=(p+z2/(2.0*trials))/den
    margin=(z*math.sqrt((p*(1.0-p)+z2/(4.0*trials))/trials))/den
    return max(0.0,center-margin)

def _future_reuse_estimate(case:OptimizationCase,sequence:int)->int:
    if sequence <= 0 or case.observed_count <= 0:
        return 0
    arrival_lower=_wilson_lower(case.observed_count,sequence)
    eligibility_lower=_wilson_lower(case.eligible_reuse_count,case.observed_count)
    return int(POLICY_HORIZON_REQUESTS*arrival_lower*eligibility_lower)

def decide(case:OptimizationCase,family:str,sequence:int|None=None)->OptimizationCase:
    contract=CONTRACTS[family]; cost=DEFAULTS[family]
    case.validation_cost_estimate_micro=cost.validation_micro
    case.maintenance_cost_estimate_micro=cost.maintenance_micro
    if not contract.optimizable:
        case.decision="REASON_ONLY"; case.decision_reason="TASK_NOT_SAFELY_REDUCIBLE"; return case
    if case.observed_count < MIN_OBSERVATIONS:
        case.decision="DEFER"; case.decision_reason="INSUFFICIENT_EVIDENCE"; return case
    sequence=sequence if sequence is not None else case.observed_count
    case.future_reuse_estimate=_future_reuse_estimate(case,sequence)
    drift_rate_ppm=(case.drift_events_observed*1_000_000)//max(1,case.observed_count)
    if drift_rate_ppm > contract.max_drift_rate_ppm:
        case.decision="REASON_ONLY"; case.decision_reason="OBSERVED_DRIFT_TOO_HIGH"; return case
    case.safe_probability_ppm=max(200_000,1_000_000-drift_rate_ppm*3)
    cr=case.reasoning_cost_estimate_micro or DEFAULT_REASONING_ESTIMATE_MICRO
    per=max(0,cr-cost.deterministic_execution_micro)
    case.expected_reuse_value_micro=(case.future_reuse_estimate*case.safe_probability_ppm*per)//1_000_000
    expected_relearning=(cost.relearning_micro*drift_rate_ppm)//1_000_000
    case.expected_optimization_cost_micro=(cost.acquisition_micro+cost.validation_micro+cost.maintenance_micro+expected_relearning+SAFETY_MARGIN_MICRO)
    if case.expected_reuse_value_micro > case.expected_optimization_cost_micro:
        case.decision="PROMOTE"; case.decision_reason="BREAK_EVEN_CLEARED"
    else:
        case.decision="DEFER"; case.decision_reason="BREAK_EVEN_NOT_YET_CLEARED"
    return case
