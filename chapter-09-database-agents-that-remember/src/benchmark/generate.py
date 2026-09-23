from __future__ import annotations
import json,hashlib
from pathlib import Path
from src.database.executor import execute
from src.database.queries import QUERIES
FAMILIES=['sales.customer_revenue','sales.order_status','inventory.low_stock','procurement.supplier_spend','logistics.late_shipments','finance.invoice_aging']
CHANGED=set(['sales.customer_revenue','inventory.low_stock','procurement.supplier_spend','logistics.late_shipments'])
LABELS=['demand_decline','fulfillment_risk','payment_risk','supplier_risk','other','none']
def params(f,i):
    if f=='sales.customer_revenue': return {'customer_id':f'C{(i%6)+1:03}','start_date':'2026-01-01','end_date':'2026-06-30'}
    if f=='sales.order_status': return {'status':['OPEN','SHIPPED','CLOSED'][i%3],'start_date':'2026-01-01','end_date':'2026-06-30'}
    if f=='inventory.low_stock': return {'warehouse_id':['W1','W2'][i%2]}
    if f=='procurement.supplier_spend': return {'supplier_id':f'S{(i%4)+1:03}','start_date':'2026-01-01','end_date':'2026-06-30'}
    if f=='logistics.late_shipments': return {'start_date':'2026-04-01','end_date':'2026-04-30'}
    return {'as_of_date':'2026-06-30'}
def make_row(n,f,phase,version,reasoning,db_path):
    p=params(f,n); expected,_=execute(db_path,QUERIES[(f,version)],p); label=LABELS[FAMILIES.index(f)] if reasoning else None
    q=f"HarborPoint question for {f} using parameters {p}." + (f" Semantic reasoning required. EXCEPTION_NOTE={label}." if reasoning else '')
    return {'request_id':f'CH9-{n:03}','phase':phase,'query_family':f,'contract_version':version,'family_contract_version':('V2' if version=='V2' and f in CHANGED else 'V1'),'parameters':p,'question':q,'reasoning_required':reasoning,'semantic_note':label or 'none','semantic_label':label,'affected_by_drift':version=='V2' and f in CHANGED,'expected_result':expected}
def generate(db_v1,db_v2):
    rows=[]; n=1
    for f in FAMILIES:
      for _ in range(10): rows.append(make_row(n,f,'A','V1',False,db_v1)); n+=1
    for f in FAMILIES:
      for j in range(5): rows.append(make_row(n,f,'B','V1',j<3,db_v1)); n+=1
    for f in FAMILIES:
      count=8 if f in CHANGED else 14
      for _ in range(count): rows.append(make_row(n,f,'C','V2',False,db_v2)); n+=1
    assert len(rows)==150 and sum(r['reasoning_required'] for r in rows)==18
    demo=[rows[i] for i in [0,1,10,11,20,21,30,31,60,61,62,90,91,98,122]]
    return rows,demo
