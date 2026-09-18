from __future__ import annotations
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
ALIASES={
 "invoice.northstar":{"subtotal":"AMOUNT_BEFORE_TAX","tax":"TAX_AMOUNT","total":"AMOUNT_DUE"},
 "purchase_order.harborpoint":{"line_items":"ITEMS_V2"},
 "shipping_notice.blueriver":{"tracking_number":"TRACKING_ID","package_count":"PACKAGES_TOTAL"},
 "remittance.meridian":{"invoice_references":"ALLOCATION_TABLE"},
}
def write_pdf(path:Path,lines:list[str]):
    path.parent.mkdir(parents=True,exist_ok=True); c=canvas.Canvas(str(path),pagesize=LETTER); y=750
    for line in lines:
        c.drawString(54,y,line); y-=18
        if y<54: c.showPage(); y=750
    c.save()
def render_lines(family,version,fields,note=None):
    changed=version=="V2" and family in ALIASES; lines=[f"HARBORPOINT SYNTHETIC | {family} | {version}",f"TEMPLATE-CONTRACT: {version if changed else 'V1'}",f"FORMAT: {'REVISED' if changed else 'STANDARD'}"]
    aliases=ALIASES.get(family,{}) if changed else {}
    for k,v in fields.items():
        key=aliases.get(k,k.upper())
        if k in {"line_items","invoice_references"}: lines.append(f"{key}: {json_dumps(v)}")
        else: lines.append(f"{key}: {v}")
    if note is not None: lines.append(f"EXCEPTION_NOTE: {note}")
    return lines
def json_dumps(v):
    import json; return json.dumps(v,separators=(",",":"))
