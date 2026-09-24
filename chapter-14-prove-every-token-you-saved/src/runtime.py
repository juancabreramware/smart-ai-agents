def execute(req, operation):
    """Trusted closed deterministic runtime using public operational semantics only."""
    p=req.payload
    if operation=="inventory_reorder":
        return p["on_hand"]-p["reserved"] < p["reorder_point"]
    if operation=="shipment_escalate":
        return p["elapsed_hours"] > 48 and p["priority"]
    if operation=="invoice_escalate":
        if req.contract_version=="v1":
            return p["amount"] >= 5000 and p["days_open"] >= 10
        if req.contract_version=="v2":
            return p["amount"] >= 4000 and p["days_open"] >= 7
    if operation=="supplier_review":
        if req.contract_version=="v1":
            score=.60*p["quality"]+.40*p["delivery"]; return score < 82
        if req.contract_version=="v2":
            score=.45*p["quality"]+.55*p["delivery"]; return score < 85
    if operation=="customer_manual_review":
        return p["risk_score"] >= 70 or p["dispute"]
    if operation=="order_priority":
        if req.contract_version=="v1": return p["priority"] or p["age_hours"] > 48
        if req.contract_version=="v2": return p["priority"] or p["age_hours"] > 36
    if operation=="return_approve":
        return p["days_since_delivery"] <= 30 and not p["damaged"]
    if operation=="capacity_overflow":
        return p["projected_units"] > p["capacity_units"]
    raise ValueError(f"Unsupported operation/version: {operation}/{req.contract_version}")
