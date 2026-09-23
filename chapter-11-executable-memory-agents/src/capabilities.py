import hashlib,json
from .models import Candidate,Capability,Decision
ALLOWED={"inventory_reorder","shipment_sla","invoice_escalation","supplier_score","customer_action","order_priority"}
def ih(op,c): return hashlib.sha256(json.dumps({"operation":op,"semantic_version":c.semantic_version,"dependencies":list(c.dependencies),"parameters":c.parameters},sort_keys=True,separators=(",",":")).encode()).hexdigest()
def execute(op,x,c,label=None):
    p=c.parameters
    if op=="inventory_reorder":
        t=x["on_hand"]-x["reserved"] < x["reorder_point"]+p["safety_buffer"]; return Decision("reorder" if t else "no_action",x["order_quantity"] if t else 0)
    if op=="shipment_sla":
        t=x["eta_hours"]>x["promised_hours"]+p["grace_hours"]; return Decision("escalate" if t else "no_action",t,label if t else None)
    if op=="invoice_escalation":
        t=x["days_overdue"]>p["days_threshold"] and x["amount"]>=p["amount_threshold"]; return Decision("escalate" if t else "no_action",t,label if t else None)
    if op=="supplier_score":
        s=round(x["on_time_pct"]*p["on_time_weight"]+x["quality_pct"]*p["quality_weight"],2); return Decision("review" if s<p["action_threshold"] else "no_action",s)
    if op=="customer_action":
        t=x["risk_score"]>p["risk_threshold"] and bool(x["past_due"]); return Decision("review" if t else "no_action",t,label if t else None)
    if op=="order_priority":
        t=x["age_hours"]>p["sla_hours"] or bool(x["priority_flag"]); return Decision("prioritize" if t else "no_action",t)
    raise ValueError("operation not allowlisted")
def validate(cand,c):
    checks=[(cand.operation in ALLOWED,"operation_not_allowlisted"),(cand.family==c.family,"family_mismatch"),(cand.operation==c.operation,"operation_mismatch"),
            (tuple(cand.dependencies)==c.dependencies,"dependency_mismatch"),(cand.policy_fingerprint==c.policy_fingerprint,"policy_mismatch"),
            (cand.environment_fingerprint==c.environment_fingerprint,"environment_mismatch")]
    for ok,r in checks:
        if not ok:return False,r
    return True,"validated"
def promote(cand,c,version):
    ok,r=validate(cand,c)
    if not ok: raise ValueError(r)
    return Capability(f"{c.family}.capability",version,c.family,c.version,c.operation,c.dependencies,c.policy_fingerprint,c.environment_fingerprint,ih(c.operation,c),provenance=cand.provenance)
