from __future__ import annotations
from .models import Request, Answer
from .contracts import OPERATION_BY_FAMILY, ALLOWED_OPERATIONS

def execute(operation:str, r:Request)->Answer:
    if operation not in ALLOWED_OPERATIONS:
        raise ValueError(f"operation not allowed: {operation}")
    p=r.payload
    if operation=="inventory_reorder":
        value=(p["on_hand"]-p["reserved"]) < p["reorder_point"]
    elif operation=="shipment_escalate":
        value=(p["elapsed_hours"]>48) and p["priority"]
    elif operation=="invoice_escalate":
        value=(p["amount"]>=5000 and p["days_open"]>=10) if r.version=="v1" else (p["amount"]>=4000 and p["days_open"]>=7)
    elif operation=="supplier_review":
        score=round((.60*p["quality"]+.40*p["delivery"]) if r.version=="v1" else (.45*p["quality"]+.55*p["delivery"]),2)
        value=score < (82 if r.version=="v1" else 85)
    elif operation=="customer_manual_review":
        value=p["risk_score"]>=70 or p["dispute"]
    elif operation=="order_priority":
        value=p["priority"] or p["age_hours"]>(48 if r.version=="v1" else 36)
    elif operation=="return_approve":
        value=p["days_since_delivery"]<=30 and not p["damaged"]
    elif operation=="capacity_overflow":
        value=p["projected_units"]>p["capacity_units"]
    else:
        raise ValueError(operation)
    return Answer(bool(value))

def validate_typed(answer:Answer)->bool:
    return type(answer.value) is bool

def validate_candidate(operation:str, r:Request, answer:Answer)->bool:
    if operation != OPERATION_BY_FAMILY[r.family]:
        return False
    if not validate_typed(answer):
        return False
    # Validation is against trusted deterministic operational semantics,
    # not hidden scoring data and not an LLM self-assessment.
    return execute(operation,r).value == answer.value
