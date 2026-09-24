import random, hashlib, json
from .models import Request

WORKLOAD_VERSION="chapter14-workload-v1.0.0"
SEED=140014
FAMILIES=("inventory","shipment","invoice","supplier","customer","order","returns","capacity")
REASONING_REQUIRED={19,47,78,111,139,168,205,231}
# Stress events are frozen by sequence, not selected after seeing results.
RETRY_SEQS={127,151,214}
HARD_FAIL_SEQS={145}
P2_START=181

def _payload(f,r):
    if f=="inventory": return {"on_hand":r.randint(20,140),"reserved":r.randint(0,30),"reorder_point":r.randint(25,90)}
    if f=="shipment": return {"elapsed_hours":r.randint(12,90),"priority":bool(r.getrandbits(1))}
    if f=="invoice": return {"amount":r.randint(1000,9000),"days_open":r.randint(1,20)}
    if f=="supplier": return {"quality":r.randint(65,100),"delivery":r.randint(65,100)}
    if f=="customer": return {"risk_score":r.randint(20,95),"dispute":bool(r.getrandbits(1))}
    if f=="order": return {"priority":bool(r.getrandbits(1)),"age_hours":r.randint(4,80)}
    if f=="returns": return {"days_since_delivery":r.randint(1,50),"damaged":bool(r.getrandbits(1))}
    if f=="capacity": return {"projected_units":r.randint(60,180),"capacity_units":r.randint(80,150)}

def build_workload(count=240):
    r=random.Random(SEED); out=[]
    # Four deterministic waves; later families appear but future mix is not exposed to routing.
    mixes=[
      ["inventory","shipment","invoice","supplier","customer","order"]*10,
      ["inventory","shipment","invoice","supplier","customer","order","returns","inventory","shipment","returns"]*6,
      ["inventory","shipment","invoice","supplier","customer","order","returns","invoice","supplier","order"]*6,
      ["inventory","shipment","invoice","supplier","customer","order","returns","capacity","returns","capacity"]*6,
    ]
    seq=0
    for wave,mix in enumerate(mixes,1):
        for f in mix:
            seq+=1
            if seq>count: break
            ver="v2" if wave>=3 and f in {"invoice","supplier","order"} else "v1"
            fm="retry_once" if seq in RETRY_SEQS else ("hard_fail_once" if seq in HARD_FAIL_SEQS else None)
            out.append(Request(f"REQ-{seq:04d}",seq,wave,f,ver,_payload(f,r),seq in REASONING_REQUIRED,fm,"P2" if seq>=P2_START else "P1"))
    return out[:count]

def canonical_json(reqs):
    rows=[{"request_id":x.request_id,"seq":x.seq,"wave":x.wave,"family":x.family,"contract_version":x.contract_version,
           "payload":x.payload,"reasoning_required":x.reasoning_required,"failure_mode":x.failure_mode,"pricing_epoch":x.pricing_epoch} for x in reqs]
    return json.dumps(rows,sort_keys=True,separators=(",",":"))

def workload_hash(reqs): return hashlib.sha256(canonical_json(reqs).encode()).hexdigest()
