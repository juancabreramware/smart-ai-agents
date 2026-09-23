from .evidence import read_jsonl
from .workload import build,workload_hash
from .contracts import drifted_families
def audit(d):
    ps={a:d/f"{a}.jsonl" for a in ("baseline","naive","smart")}
    if not all(p.exists() for p in ps.values()):return {"passed":False,"errors":["missing architecture ledger"]}
    L={a:read_jsonl(p) for a,p in ps.items()};n=len(L["baseline"]);expected_n=15 if n==15 else 150;h=workload_hash(build(expected_n));errs=[];ids=[x["request_id"] for x in L["baseline"]]
    for a,rows in L.items():
        if len(rows)!=expected_n:errs.append(f"{a}: row count")
        if [x["request_id"] for x in rows]!=ids:errs.append(f"{a}: request order")
        if any(x["workload_hash"]!=h for x in rows):errs.append(f"{a}: workload hash")
    s=L["smart"]
    if any(x["route"]=="deterministic_reuse" and (x["llm_called"] or x["input_tokens"] or x["output_tokens"]) for x in s):errs.append("hidden LLM on deterministic reuse")
    if expected_n==150:
        routes={k:sum(x["route"]==k for x in s) for k in {x["route"] for x in s}}
        if routes!={"initial_acquisition":6,"reasoning_required":18,"relearning":4,"deterministic_reuse":122}:errs.append(f"smart routes {routes}")
        if sum(x["llm_called"] for x in L["baseline"])!=150:errs.append("baseline calls")
        if sum(x["llm_called"] for x in s)!=28:errs.append("smart calls")
        if sum(x["llm_called"] for x in L["naive"])!=24:errs.append("naive calls")
        if {x["family"] for x in s if x["route"]=="relearning"}!=drifted_families():errs.append("selective relearning")
    rec={a:{"rows":len(r),"correct":sum(x["correct"] for x in r),"llm_calls":sum(x["llm_called"] for x in r),"stale_reuse":sum(x["stale_reuse"] for x in r),"cost_usd":round(sum(float(x["measured_llm_cost_usd"]) for x in r),10)} for a,r in L.items()}
    return {"passed":not errs,"errors":errs,"recomputed":rec,"run_id":L["baseline"][0]["run_id"]}
