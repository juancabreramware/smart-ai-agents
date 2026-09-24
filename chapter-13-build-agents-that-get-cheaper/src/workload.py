from __future__ import annotations
import hashlib, json, random
from .models import Request

WORKLOAD_VERSION="chapter13-workload-v1.0.0"
SEED=130013

# Frozen family counts by wave. Each wave has exactly 60 requests.
WAVE_COUNTS={
  1: {"inventory":12,"shipment":11,"invoice":10,"supplier":10,"customer":9,"order":8},
  2: {"inventory":10,"shipment":10,"invoice":9,"supplier":9,"customer":8,"order":8,"returns":6},
  3: {"inventory":9,"shipment":9,"invoice":10,"supplier":10,"customer":7,"order":10,"returns":5},
  4: {"inventory":8,"shipment":8,"invoice":7,"supplier":7,"customer":7,"order":7,"returns":8,"capacity":8},
}

# Reasoning-required exceptions remain intentionally on the model path.
EXCEPTION_SEQUENCES={23,47,74,109,137,166,203,228}

def version_for(family:str,wave:int)->str:
    if wave>=3 and family in {"invoice","supplier","order"}:
        return "v2"
    return "v1"

def _payload(family:str, rng:random.Random, seq:int)->dict:
    if family=="inventory":
        return {"on_hand":rng.randint(20,160),"reserved":rng.randint(0,40),"reorder_point":rng.randint(25,90)}
    if family=="shipment":
        return {"elapsed_hours":rng.randint(12,96),"priority":bool(rng.randint(0,1))}
    if family=="invoice":
        return {"amount":rng.randint(500,9000),"days_open":rng.randint(1,25)}
    if family=="supplier":
        return {"quality":rng.randint(65,100),"delivery":rng.randint(65,100)}
    if family=="customer":
        return {"risk_score":rng.randint(20,95),"dispute":bool(rng.randint(0,4)==0)}
    if family=="order":
        return {"age_hours":rng.randint(6,80),"priority":bool(rng.randint(0,3)==0)}
    if family=="returns":
        return {"days_since_delivery":rng.randint(1,60),"damaged":bool(rng.randint(0,5)==0)}
    if family=="capacity":
        cap=rng.randint(500,1400); return {"capacity_units":cap,"projected_units":rng.randint(350,1650)}
    raise KeyError(family)

def build()->list[Request]:
    rng=random.Random(SEED)
    out=[]; seq=1
    for wave in range(1,5):
        families=[]
        for family,count in WAVE_COUNTS[wave].items():
            families.extend([family]*count)
        rng.shuffle(families)
        for family in families:
            out.append(Request(
                request_id=f"REQ-{seq:03d}", sequence=seq, wave=wave, family=family,
                version=version_for(family,wave), payload=_payload(family,rng,seq),
                reasoning_required=seq in EXCEPTION_SEQUENCES,
            ))
            seq+=1
    assert len(out)==240
    return out

def public_record(r:Request)->dict:
    return {
        "request_id":r.request_id,"sequence":r.sequence,"wave":r.wave,
        "family":r.family,"version":r.version,"payload":r.payload,
        "reasoning_required":r.reasoning_required,
    }

def workload_hash(workload:list[Request]|None=None)->str:
    w=workload or build()
    raw=json.dumps([public_record(r) for r in w],sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()
