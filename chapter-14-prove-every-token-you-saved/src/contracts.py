import hashlib, json
CONTRACT_VERSION = "chapter14-public-contract-v1.0.0"

PUBLIC_CONTRACTS = {
 ("inventory","v1"): {"operation":"inventory_reorder","rule":"available = on_hand - reserved; reorder iff available < reorder_point"},
 ("shipment","v1"): {"operation":"shipment_escalate","rule":"late iff elapsed_hours > 48; escalate iff late and priority"},
 ("invoice","v1"): {"operation":"invoice_escalate","rule":"escalate iff amount >= 5000 and days_open >= 10"},
 ("invoice","v2"): {"operation":"invoice_escalate","rule":"escalate iff amount >= 4000 and days_open >= 7"},
 ("supplier","v1"): {"operation":"supplier_review","rule":"score=.60*quality+.40*delivery; review iff score < 82"},
 ("supplier","v2"): {"operation":"supplier_review","rule":"score=.45*quality+.55*delivery; review iff score < 85"},
 ("customer","v1"): {"operation":"customer_manual_review","rule":"manual review iff risk_score >= 70 or dispute"},
 ("order","v1"): {"operation":"order_priority","rule":"priority iff priority flag or age_hours > 48"},
 ("order","v2"): {"operation":"order_priority","rule":"priority iff priority flag or age_hours > 36"},
 ("returns","v1"): {"operation":"return_approve","rule":"approve iff days_since_delivery <= 30 and not damaged"},
 ("capacity","v1"): {"operation":"capacity_overflow","rule":"overflow iff projected_units > capacity_units"},
}
ALLOWLIST={v["operation"] for v in PUBLIC_CONTRACTS.values()}

def public_contract(family, version):
    return PUBLIC_CONTRACTS[(family,version)]

PUBLIC_CONTRACT_HASH=hashlib.sha256(json.dumps([{"family":k[0],"version":k[1],**v} for k,v in sorted(PUBLIC_CONTRACTS.items())],sort_keys=True,separators=(",",":")).encode()).hexdigest()
