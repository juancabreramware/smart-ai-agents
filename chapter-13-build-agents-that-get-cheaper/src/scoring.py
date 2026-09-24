from __future__ import annotations
from .models import Request, Answer

# Scoring-only ground truth. Real provider code does not import this module.
def ground_truth(r:Request)->Answer:
    p=r.payload
    if r.family=="inventory":
        value=(p["on_hand"]-p["reserved"]) < p["reorder_point"]
    elif r.family=="shipment":
        value=(p["elapsed_hours"]>48) and p["priority"]
    elif r.family=="invoice":
        if r.version=="v1": value=p["amount"]>=5000 and p["days_open"]>=10
        else: value=p["amount"]>=4000 and p["days_open"]>=7
    elif r.family=="supplier":
        if r.version=="v1": score=round(.60*p["quality"]+.40*p["delivery"],2); value=score<82
        else: score=round(.45*p["quality"]+.55*p["delivery"],2); value=score<85
    elif r.family=="customer":
        value=p["risk_score"]>=70 or p["dispute"]
    elif r.family=="order":
        threshold=48 if r.version=="v1" else 36
        value=p["priority"] or p["age_hours"]>threshold
    elif r.family=="returns":
        value=p["days_since_delivery"]<=30 and not p["damaged"]
    elif r.family=="capacity":
        value=p["projected_units"]>p["capacity_units"]
    else:
        raise KeyError(r.family)
    return Answer(bool(value))
