from pathlib import Path
import sys
_PROJECT_ROOT=Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path: sys.path.insert(0,str(_PROJECT_ROOT))

import copy,json,shutil,tempfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from scripts.audit_evidence import audit
SRC=ROOT/"evidence/benchmark-mock-v1"
if not SRC.exists(): raise SystemExit("Run mock benchmark first.")
def loadj(p): return json.loads(p.read_text(encoding="utf-8"))
def savej(p,x): p.write_text(json.dumps(x,indent=2,sort_keys=True),encoding="utf-8")
def loadjl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
def savejl(p,x): p.write_text("".join(json.dumps(y,sort_keys=True)+"\n" for y in x),encoding="utf-8")
def audit_fails(d):
    return not audit(d)["passed"]
cases=[]
def run(name,fn):
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/"e"; shutil.copytree(SRC,d); fn(d); ok=audit_fails(d); cases.append((name,ok))
run("delete provider attempt",lambda d: savejl(d/"provider_attempts.jsonl",loadjl(d/"provider_attempts.jsonl")[1:]))
run("duplicate request",lambda d: (lambda x: savejl(d/"workload.jsonl",x+[x[0]]))(loadjl(d/"workload.jsonl")))
def token(d):
    x=loadjl(d/"provider_attempts.jsonl"); x[0]["input_tokens"]+=1; savejl(d/"provider_attempts.jsonl",x)
run("change token count",token)
def pricing(d):
    x=loadj(d/"pricing_manifest.json"); x["pricing"]["P1"]["gpt-5-mini"]["input_per_million"]+=1; savej(d/"pricing_manifest.json",x)
run("change pricing",pricing)
def workload(d):
    x=loadjl(d/"workload.jsonl"); x[0]["payload"]["on_hand"]=999999; savejl(d/"workload.jsonl",x)
run("change workload",workload)
def avoided(d):
    x=loadjl(d/"smart_request_ledger.jsonl"); x[0]["route"]="deterministic_reuse"; x[0]["attempts"]=0; savejl(d/"smart_request_ledger.jsonl",x)
run("fabricate avoided call",avoided)
def drop_retry(d):
    x=loadjl(d/"provider_attempts.jsonl"); idx=next(i for i,y in enumerate(x) if y["status"]=="failed"); del x[idx]; savejl(d/"provider_attempts.jsonl",x)
run("drop retry",drop_retry)
def summary(d):
    x=loadj(d/"evidence_grade_report.json"); x["provider_savings_micro"]+=1; savej(d/"evidence_grade_report.json",x)
run("edit summary",summary)
def contract(d):
    x=loadj(d/"manifest.json"); x["public_contract_hash"]="0"*64; savej(d/"manifest.json",x)
run("modify public contract hash",contract)
def future(d):
    x=loadjl(d/"workload.jsonl"); x[0]["future_drift_hint"]="v2"; savejl(d/"workload.jsonl",x)
run("inject future field",future)
for n,ok in cases: print(("PASS" if ok else "FAIL"),n)
if not all(ok for _,ok in cases): raise SystemExit(1)
print(f"{len(cases)}/{len(cases)} negative tamper tests passed")
