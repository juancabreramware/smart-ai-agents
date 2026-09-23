from __future__ import annotations
import hashlib, json, random
from .models import Request
from .contracts import FAMILIES, version_for

# Fixed family quotas per phase; totals are exactly 30 per family and 180 overall.
PHASE_QUOTAS = [
    # discovery 1..36
    {"stable_recurring":10,"stable_rare":8,"volatile_recurring":8,"high_validation_recurring":6,"ambiguous_judgment":3,"emerging_pattern":1},
    # pattern formation 37..90
    {"stable_recurring":10,"stable_rare":10,"volatile_recurring":9,"high_validation_recurring":10,"ambiguous_judgment":10,"emerging_pattern":5},
    # drift/maintenance 91..132
    {"stable_recurring":5,"stable_rare":7,"volatile_recurring":8,"high_validation_recurring":7,"ambiguous_judgment":8,"emerging_pattern":7},
    # mature 133..180
    {"stable_recurring":5,"stable_rare":5,"volatile_recurring":5,"high_validation_recurring":7,"ambiguous_judgment":9,"emerging_pattern":17},
]
PHASE_LENGTHS=(36,54,42,48)

def _phase_order(q:dict[str,int], seed:int)->list[str]:
    bag=[]
    for f,n in q.items(): bag += [f]*n
    random.Random(seed).shuffle(bag)
    return bag

def build(count:int=180)->list[Request]:
    if count!=180: raise ValueError("Canonical workload is exactly 180 requests.")
    order=[]
    for i,q in enumerate(PHASE_QUOTAS): order += _phase_order(q,1200+i)
    seen={f:0 for f in FAMILIES}
    out=[]
    for seq,f in enumerate(order,1):
        seen[f]+=1; n=seen[f]; rng=random.Random(120000+seq*97+n*13)
        if f=="stable_recurring":
            p={"on_hand":rng.randint(5,100),"reserved":rng.randint(0,20),"reorder_point":rng.randint(20,55)}
        elif f=="stable_rare":
            p={"amount":rng.randint(1000,9000),"days_open":rng.randint(1,20)}
        elif f=="volatile_recurring":
            p={"age_hours":rng.randint(18,65),"priority":rng.random()<.16}
        elif f=="high_validation_recurring":
            p={"quality":rng.randint(65,100),"delivery":rng.randint(65,100)}
        elif f=="ambiguous_judgment":
            p={"risk":rng.randint(45,85),"past_due":rng.random()<.35,"dispute":rng.random()<.25,"tenure_years":rng.randint(0,10)}
        else:
            p={"eta_hours":rng.randint(10,72),"promised_hours":rng.randint(12,48)}
        out.append(Request(f"REQ-{seq:03d}",seq,f,version_for(f,seq),p,True))
    assert len(out)==180 and all(sum(r.family==f for r in out)==30 for f in FAMILIES)
    return out

def workload_hash(rows:list[Request]|None=None)->str:
    rows=rows or build()
    payload="\n".join(json.dumps(r.public_dict(),sort_keys=True,separators=(",",":")) for r in rows).encode()
    return hashlib.sha256(payload).hexdigest()
