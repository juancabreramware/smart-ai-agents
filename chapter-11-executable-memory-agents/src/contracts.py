import hashlib,json
from .models import Contract
def _fp(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def _c(f,v,sv,op,deps,p):
    pub={"family":f,"version":v,"semantic_version":sv,"operation":op,"dependencies":list(deps),"parameters":p}
    return Contract(f,v,sv,op,tuple(deps),p,_fp(pub))
V1={
"inventory_planning":_c("inventory_planning","V1","inventory-policy-1","inventory_reorder",("on_hand","reserved","reorder_point","order_quantity"),{"safety_buffer":0}),
"shipment_sla":_c("shipment_sla","V1","shipment-policy-1","shipment_sla",("eta_hours","promised_hours"),{"grace_hours":0}),
"invoice_escalation":_c("invoice_escalation","V1","invoice-policy-1","invoice_escalation",("days_overdue","amount"),{"days_threshold":7,"amount_threshold":1000}),
"supplier_scorecard":_c("supplier_scorecard","V1","supplier-policy-1","supplier_score",("on_time_pct","quality_pct"),{"on_time_weight":.6,"quality_weight":.4,"action_threshold":80}),
"customer_account":_c("customer_account","V1","customer-policy-1","customer_action",("risk_score","past_due"),{"risk_threshold":70}),
"order_operations":_c("order_operations","V1","order-policy-1","order_priority",("age_hours","priority_flag"),{"sla_hours":48})}
V2={
"inventory_planning":_c("inventory_planning","V2","inventory-policy-2","inventory_reorder",("on_hand","reserved","reorder_point","order_quantity"),{"safety_buffer":5}),
"shipment_sla":V1["shipment_sla"],
"invoice_escalation":_c("invoice_escalation","V2","invoice-policy-2","invoice_escalation",("days_overdue","amount"),{"days_threshold":5,"amount_threshold":750}),
"supplier_scorecard":_c("supplier_scorecard","V2","supplier-policy-2","supplier_score",("on_time_pct","quality_pct"),{"on_time_weight":.4,"quality_weight":.6,"action_threshold":85}),
"customer_account":V1["customer_account"],
"order_operations":_c("order_operations","V2","order-policy-2","order_priority",("age_hours","priority_flag"),{"sla_hours":36})}
def get_contract(f,v): return (V1 if v=="V1" else V2)[f]
def public_contract(f,v):
    c=get_contract(f,v)
    return {"family":c.family,"requested_version":v,"effective_contract_version":c.version,"semantic_version":c.semantic_version,
            "operation":c.operation,"dependencies":list(c.dependencies),"parameters":c.parameters,
            "policy_fingerprint":c.policy_fingerprint,"environment_fingerprint":c.environment_fingerprint}
def drifted_families(): return {f for f in V1 if V1[f].policy_fingerprint!=V2[f].policy_fingerprint}
