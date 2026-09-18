from __future__ import annotations
import json
ALIASES={
 "invoice.northstar":{"subtotal":"amount_before_tax","tax":"tax_amount","total":"amount_due"},
 "purchase_order.harborpoint":{"line_items":"items_v2"},
 "shipping_notice.blueriver":{"tracking_number":"tracking_id","package_count":"packages_total"},
 "remittance.meridian":{"invoice_references":"allocation_table"},
}
def deterministic_extract(text:str, required:list[str], family:str|None=None, version:str="V1")->dict:
    by={}
    for line in text.splitlines():
        if ':' in line:
            k,v=line.split(':',1); by[k.strip().lower()]=v.strip()
    aliases=ALIASES.get(family,{}) if version=="V2" else {}
    out={}
    for f in required:
        key=aliases.get(f,f); val=by.get(key)
        if f in {"line_items","invoice_references"} and val:
            try: val=json.loads(val)
            except Exception: pass
        out[f]=val
    return out
