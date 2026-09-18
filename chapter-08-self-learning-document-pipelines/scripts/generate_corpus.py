from __future__ import annotations
import hashlib,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.documents.generator import write_pdf,render_lines
FAMS=['invoice.northstar','invoice.redwood','purchase_order.harborpoint','shipping_notice.blueriver','remittance.meridian','tax_form.w9']
CHANGED=set(['invoice.northstar','purchase_order.harborpoint','shipping_notice.blueriver','remittance.meridian'])
SEM=['pricing_dispute','quantity_dispute','address_exception','tax_exception','other','none']
NOTES={'pricing_dispute':'Customer disputes pricing on the referenced charge.','quantity_dispute':'Received quantity does not match the stated quantity.','address_exception':'Delivery address requires review before processing.','tax_exception':'Tax treatment requires review.','other':'Manual business review requested for an unusual exception.','none':'No exception reported.'}
def fields(f,i,v):
    a=f'{100+i}.00'; tax=f'{10+i%5}.00'; total=f'{110+i+i%5}.00'
    if f=='invoice.northstar': return {'invoice_number':f'NS-{i:05d}','vendor_id':'VEN-NS','invoice_date':'2026-08-01','due_date':'2026-09-01','po_number':f'PO-{i:05d}','subtotal':a,'tax':tax,'total':total,'currency':'USD'}
    if f=='invoice.redwood': return {'invoice_number':f'RW-{i:05d}','account_number':'ACCT-RW','invoice_date':'2026-08-02','service_period':'2026-07','subtotal':a,'fees':'5.00','tax':tax,'total':f'{115+i+i%5}.00','currency':'USD'}
    if f=='purchase_order.harborpoint': return {'po_number':f'PO-{i:05d}','supplier_id':'SUP-HP','order_date':'2026-08-03','buyer':'Alex Morgan','ship_to':'HarborPoint DC 4','line_items':[{'sku':f'SKU-{i:04d}','quantity':2,'unit_price':'25.00'}],'subtotal':'50.00','total':'50.00'}
    if f=='shipping_notice.blueriver': return {'shipment_id':f'SHP-{i:05d}','carrier':'BlueRiver Freight','tracking_number':f'TRK{i:08d}','po_number':f'PO-{i:05d}','ship_date':'2026-08-04','expected_delivery':'2026-08-07','package_count':str(1+i%4)}
    if f=='remittance.meridian': return {'payment_id':f'PAY-{i:05d}','payment_date':'2026-08-05','payer':'Meridian Retail','invoice_references':[f'INV-{i:05d}'] if v=='V1' else [f'INV-{i:05d}',f'INV-{i+1:05d}'],'gross_amount':'500.00','deductions':'20.00','net_amount':'480.00'}
    return {'legal_name':f'Synthetic Vendor {i}','business_name':f'Vendor DBA {i}','tax_classification':'LLC','address':f'{100+i} Example Ave, Orlando FL','tin_type':'EIN','masked_tin':f'XX-XXX{i%10000:04d}'}
def build():
    docs=ROOT/'documents'; docs.mkdir(exist_ok=True); workload=[]; idx=0
    # A 10/family, B 5/family, C 8 affected +14 unchanged.
    plan=[]
    for f in FAMS:
        for _ in range(10): plan.append(('A','V1',f,False))
    for f in FAMS:
        for j in range(5): plan.append(('B','V1',f,j<3))
    for f in FAMS:
        count=8 if f in CHANGED else 14
        for _ in range(count): plan.append(('C','V2',f,False))
    assert len(plan)==150 and sum(x[3] for x in plan)==18
    for idx,(phase,v,f,rr) in enumerate(plan,1):
        vals=fields(f,idx,v); label=SEM[(idx-1)%len(SEM)] if rr else None; note=NOTES[label] if rr else None
        rel=Path('documents')/v.lower()/f.replace('.','_')/f'CH8-{idx:03d}.pdf'; path=ROOT/rel
        write_pdf(path,render_lines(f,v,vals,note))
        workload.append({'request_id':f'CH8-{idx:03d}','phase':phase,'contract_version':v,'family_id':f,'reasoning_required':rr,'semantic_label':label,'affected_by_drift':v=='V2' and f in CHANGED,'document_path':rel.as_posix(),'expected_fields':vals})
    (ROOT/'workloads'/'benchmark_v1.0.jsonl').write_text(''.join(json.dumps(x,separators=(',',':'))+'\n' for x in workload))
    demo=[workload[i] for i in [0,1,10,11,20,21,30,31,60,61,62,90,91,98,122]]
    (ROOT/'workloads'/'demo_v1.0.jsonl').write_text(''.join(json.dumps(x,separators=(',',':'))+'\n' for x in demo))
    # Ground truth intentionally separate. Runner uses frozen workload in this reference harness; production planners never receive expected_fields except mock.
    (ROOT/'workloads'/'ground-truth.jsonl').write_text(''.join(json.dumps({'request_id':x['request_id'],'expected_fields':x['expected_fields'],'semantic_label':x['semantic_label']},separators=(',',':'))+'\n' for x in workload))
    print('Generated',len(workload),'canonical PDFs and',len(demo),'demo entries')
    for p in [ROOT/'workloads'/'benchmark_v1.0.jsonl',ROOT/'workloads'/'demo_v1.0.jsonl']:
        print(p.name,hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__': build()
