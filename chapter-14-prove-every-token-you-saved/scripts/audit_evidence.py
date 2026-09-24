from pathlib import Path
import sys
_PROJECT_ROOT=Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path: sys.path.insert(0,str(_PROJECT_ROOT))

import argparse,json,hashlib
from pathlib import Path
from src.accounting import provider_cost_micro,stable_hash
from src.contracts import PUBLIC_CONTRACT_HASH

def jl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
def js(p): return json.loads(p.read_text(encoding="utf-8"))
def canonical_workload_hash(rows):
    return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def audit(d):
    d=Path(d); errors=[]
    reqd=["manifest.json","workload.jsonl","ground_truth.jsonl","baseline_request_ledger.jsonl",
          "smart_request_ledger.jsonl","provider_attempts.jsonl","pricing_manifest.json",
          "cost_manifest.json","failure_schedule.json","evidence_grade_report.json"]
    for n in reqd:
        if not (d/n).exists(): errors.append("missing:"+n)
    if errors: return {"passed":False,"errors":errors}
    m=js(d/"manifest.json"); work=jl(d/"workload.jsonl"); gtrows=jl(d/"ground_truth.jsonl")
    gt={x["request_id"]:x["answer"] for x in gtrows}; b=jl(d/"baseline_request_ledger.jsonl")
    s=jl(d/"smart_request_ledger.jsonl"); a=jl(d/"provider_attempts.jsonl")
    ids=[x["request_id"] for x in work]
    if len(work)!=m["request_count"]: errors.append("request_count mismatch")
    if m.get("mode")=="canonical" and len(work)!=240: errors.append("canonical must contain exactly 240 requests")
    if len(ids)!=len(set(ids)): errors.append("duplicate workload request_id")
    if canonical_workload_hash(work)!=m["workload_hash"]: errors.append("workload hash mismatch")
    if m.get("public_contract_hash")!=PUBLIC_CONTRACT_HASH: errors.append("public contract hash mismatch")
    if set(gt)!=set(ids): errors.append("ground truth request conservation")
    for label,ledger in [("baseline",b),("smart",s)]:
        lids=[x["request_id"] for x in ledger]
        if len(lids)!=len(ids) or set(lids)!=set(ids) or len(lids)!=len(set(lids)):
            errors.append(label+" request conservation")
    aids=[x["attempt_id"] for x in a]
    if len(aids)!=len(set(aids)): errors.append("duplicate provider attempt")
    by={}
    for x in a:
        by.setdefault((x["architecture"],x["request_id"]),[]).append(x)
        if x.get("attempt_kind")=="controlled_nonbillable_failure":
            if x["input_tokens"] or x["output_tokens"] or x["provider_cost_micro"]:
                errors.append("controlled failure billed:"+x["attempt_id"])
        expected=provider_cost_micro(x["model"],x["pricing_epoch"],x["input_tokens"],x["output_tokens"])
        if expected!=x["provider_cost_micro"]: errors.append("attempt cost mismatch:"+x["attempt_id"])
    for label,ledger in [("baseline",b),("smart",s)]:
        for x in ledger:
            actual=len(by.get((label,x["request_id"]),[]))
            if actual!=x["attempts"]: errors.append("attempt conservation:"+label+":"+x["request_id"])
            expected=(x["answer"]==gt[x["request_id"]])
            if bool(x["correct"])!=expected: errors.append("correctness mismatch:"+label+":"+x["request_id"])
            if label=="smart" and x["route"]=="deterministic_reuse" and actual!=0:
                errors.append("deterministic reuse has provider attempt:"+x["request_id"])
    # Every Smart deterministic reuse must have an executed baseline counterfactual.
    for x in s:
        if x["route"]=="deterministic_reuse":
            zz=by.get(("baseline",x["request_id"]),[])
            if not any(y["status"]=="success" and y.get("attempt_kind")=="provider_attempt" for y in zz):
                errors.append("avoided call lacks successful baseline counterfactual:"+x["request_id"])
    # Frozen stress schedule must be represented in canonical evidence.
    if m.get("mode")=="canonical":
        expected_stress={x["request_id"] for x in work if x.get("failure_mode")}
        observed={x["request_id"] for x in a if x.get("attempt_kind")=="controlled_nonbillable_failure"}
        if expected_stress!=observed: errors.append("controlled failure schedule mismatch")
    def totals(arch):
        z=[x for x in a if x["architecture"]==arch]
        return {"attempts":len(z),"successful_calls":sum(x["status"]=="success" for x in z),
                "input_tokens":sum(x["input_tokens"] for x in z),
                "output_tokens":sum(x["output_tokens"] for x in z),
                "total_tokens":sum(x["input_tokens"]+x["output_tokens"] for x in z),
                "provider_cost_micro":sum(x["provider_cost_micro"] for x in z)}
    bt,st=totals("baseline"),totals("smart"); assigned=sum(x["assigned_nonprovider_cost_micro"] for x in s)
    rec={"baseline":bt,"smart":st,"correct_baseline":sum(x["correct"] for x in b),
         "correct_smart":sum(x["correct"] for x in s),"request_count":len(s),
         "deterministic_reuses":sum(x["route"]=="deterministic_reuse" for x in s),
         "provider_savings_micro":bt["provider_cost_micro"]-st["provider_cost_micro"],
         "full_benchmark_savings_micro":bt["provider_cost_micro"]-(st["provider_cost_micro"]+assigned)}
    report=js(d/"evidence_grade_report.json")
    for k,v in rec.items():
        if report.get(k)!=v: errors.append("summary mismatch:"+k)
    pricing=js(d/"pricing_manifest.json")["pricing"]; costs=js(d/"cost_manifest.json")["assigned_costs_micro"]
    if stable_hash(pricing)!=m["pricing_hash"]: errors.append("pricing hash mismatch")
    if stable_hash(costs)!=m["cost_hash"]: errors.append("cost hash mismatch")
    if m.get("mode") in {"demo","canonical"}:
        n=m["request_count"]
        if bt["successful_calls"]<=0 or st["successful_calls"]<=0: errors.append("real-provider gate: zero successful calls")
        if bt["total_tokens"]<=0 or st["total_tokens"]<=0: errors.append("real-provider gate: zero measured usage")
        if rec["correct_baseline"]!=n: errors.append(f"real-provider gate: baseline correctness {rec['correct_baseline']}/{n}")
        if rec["correct_smart"]!=n: errors.append(f"real-provider gate: smart correctness {rec['correct_smart']}/{n}")
        for (arch,rid),zz in by.items():
            if any(y["status"]=="failed" for y in zz) and not any(y["status"]=="success" for y in zz):
                errors.append("unrecovered provider failure:"+arch+":"+rid)
    result={"passed":not errors,"errors":errors,"recomputed":rec}
    (d/"audit_report.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    return result
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--evidence-dir",required=True); args=ap.parse_args()
    r=audit(args.evidence_dir); print(json.dumps(r,indent=2)); raise SystemExit(0 if r["passed"] else 1)
