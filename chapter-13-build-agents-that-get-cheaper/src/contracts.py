from __future__ import annotations
import hashlib, json

CONTRACT_VERSION = "chapter13-public-contract-v1.0.0"

# Only current family/version is supplied to the real provider.
# No future drift schedule is included in these public contracts.
PUBLIC_CONTRACTS = {
    ("inventory","v1"): "available = on_hand - reserved. reorder is true iff available < reorder_point. Return boolean reorder.",
    ("shipment","v1"): "late is true iff elapsed_hours > 48. escalate is true iff late and priority is true. Return boolean escalate.",
    ("invoice","v1"): "escalate is true iff amount >= 5000 AND days_open >= 10. Return boolean escalate.",
    ("invoice","v2"): "escalate is true iff amount >= 4000 AND days_open >= 7. Return boolean escalate.",
    ("supplier","v1"): "score = round(0.60*quality + 0.40*delivery, 2). review is true iff score < 82. Return boolean review.",
    ("supplier","v2"): "score = round(0.45*quality + 0.55*delivery, 2). review is true iff score < 85. Return boolean review.",
    ("customer","v1"): "manual_review is true iff risk_score >= 70 OR dispute is true. Return boolean manual_review.",
    ("order","v1"): "priority_action is true iff priority is true OR age_hours > 48. Return boolean priority_action.",
    ("order","v2"): "priority_action is true iff priority is true OR age_hours > 36. Return boolean priority_action.",
    ("returns","v1"): "approve_return is true iff days_since_delivery <= 30 AND damaged is false. Return boolean approve_return.",
    ("capacity","v1"): "overflow is true iff projected_units > capacity_units. Return boolean overflow.",
}

OPERATION_BY_FAMILY = {
    "inventory":"inventory_reorder",
    "shipment":"shipment_escalate",
    "invoice":"invoice_escalate",
    "supplier":"supplier_review",
    "customer":"customer_manual_review",
    "order":"order_priority",
    "returns":"return_approve",
    "capacity":"capacity_overflow",
}
ALLOWED_OPERATIONS=frozenset(OPERATION_BY_FAMILY.values())

def public_contract(family:str, version:str)->str:
    return PUBLIC_CONTRACTS[(family,version)]

def contract_manifest()->dict:
    return {
        "version": CONTRACT_VERSION,
        "contracts":[
            {"family":f,"version":v,"contract":PUBLIC_CONTRACTS[(f,v)]}
            for f,v in sorted(PUBLIC_CONTRACTS)
        ],
        "operations":dict(sorted(OPERATION_BY_FAMILY.items())),
    }

def hash_json(obj)->str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def contract_hash()->str:
    return hash_json(contract_manifest())
