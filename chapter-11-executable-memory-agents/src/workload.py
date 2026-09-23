import hashlib,json
from dataclasses import asdict
from .models import Request
F=["inventory_planning","shipment_sla","invoice_escalation","supplier_scorecard","customer_account","order_operations"]
D={91:"inventory_planning",92:"invoice_escalation",93:"supplier_scorecard",94:"order_operations"}
def inputs(f,i):
    return {
    "inventory_planning":{"on_hand":45+i%20,"reserved":10+i%7,"reorder_point":35,"order_quantity":50},
    "shipment_sla":{"eta_hours":20+i%12,"promised_hours":24},
    "invoice_escalation":{"days_overdue":3+i%9,"amount":600+i%5*250},
    "supplier_scorecard":{"on_time_pct":72+i%25,"quality_pct":76+(i*3)%20},
    "customer_account":{"risk_score":55+i%30,"past_due":bool(i%2)},
    "order_operations":{"age_hours":28+i%30,"priority_flag":bool(i%11==0)}}[f]
def build(n=150):
    if n not in (15,150):raise ValueError
    a=[]
    for i in range(1,151):
        f=D.get(i,F[(i-1)%6]); rr=i in set(range(13,31))
        a.append(Request(f"REQ-{i:03d}",i,f,"V2" if i>=91 else "V1",inputs(f,i),rr,f"exception note {i}" if rr else None,i in D))
    return a if n==150 else [a[i-1] for i in [1,2,3,4,5,6,13,14,15,91,92,93,94,95,96]]
def workload_hash(a): return hashlib.sha256("\n".join(json.dumps(asdict(r),sort_keys=True,separators=(",",":")) for r in a).encode()).hexdigest()
