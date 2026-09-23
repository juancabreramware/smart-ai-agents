from __future__ import annotations
from .models import Request, Answer

def ground_truth(r: Request) -> Answer:
    p=r.payload
    if r.family=="stable_recurring":
        value=(p["on_hand"]-p["reserved"]) < p["reorder_point"]
        return Answer("reorder" if value else "no_action", value)
    if r.family=="stable_rare":
        value=p["amount"] >= 5000 and p["days_open"] >= 10
        return Answer("escalate" if value else "no_action", value)
    if r.family=="volatile_recurring":
        threshold={1:48,2:36,3:30}[r.version]
        value=p["age_hours"] > threshold or p["priority"]
        return Answer("prioritize" if value else "no_action", value)
    if r.family=="high_validation_recurring":
        score=round(p["quality"]*.6+p["delivery"]*.4,2)
        return Answer("review" if score<82 else "approve", score)
    if r.family=="ambiguous_judgment":
        # Context-sensitive by construction: all fields matter.
        risk=p["risk"] + (12 if p["past_due"] else 0) + (8 if p["dispute"] else 0) - (6 if p["tenure_years"]>=5 else 0)
        value=risk>=72
        return Answer("manual_review" if value else "continue", value)
    if r.family=="emerging_pattern":
        value=p["eta_hours"] > p["promised_hours"] + 2
        return Answer("expedite" if value else "no_action", value)
    raise ValueError(r.family)

def is_correct(expected: Answer, actual: Answer) -> bool:
    if expected.action != actual.action: return False
    if isinstance(expected.value,bool):
        return isinstance(actual.value,bool) and actual.value is expected.value
    if isinstance(expected.value,(int,float)) and not isinstance(expected.value,bool):
        return isinstance(actual.value,(int,float)) and not isinstance(actual.value,bool) and abs(float(actual.value)-float(expected.value))<=1e-9
    return type(expected.value) is type(actual.value) and expected.value==actual.value
