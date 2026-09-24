def truth(req):
    p=req.payload; f=req.family; v=req.contract_version
    if f=="inventory": return p["on_hand"]-p["reserved"] < p["reorder_point"]
    if f=="shipment": return p["elapsed_hours"] > 48 and p["priority"]
    if f=="invoice":
        return p["amount"] >= (5000 if v=="v1" else 4000) and p["days_open"] >= (10 if v=="v1" else 7)
    if f=="supplier":
        score=(.60*p["quality"]+.40*p["delivery"]) if v=="v1" else (.45*p["quality"]+.55*p["delivery"])
        return score < (82 if v=="v1" else 85)
    if f=="customer": return p["risk_score"] >= 70 or p["dispute"]
    if f=="order": return p["priority"] or p["age_hours"] > (48 if v=="v1" else 36)
    if f=="returns": return p["days_since_delivery"] <= 30 and not p["damaged"]
    if f=="capacity": return p["projected_units"] > p["capacity_units"]
    raise KeyError(f)
