from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import json,platform,datetime,uuid,hashlib
from .workload import build,workload_hash
from .provider import make_provider
from .architectures import AlwaysReason,AlwaysOptimize,SmartSelective
from .scoring import ground_truth
from .cost_model import INPUT_USD_PER_MILLION,OUTPUT_USD_PER_MILLION,cost_profiles_dict
from .optimizer import MIN_OBSERVATIONS,SAFETY_MARGIN_MICRO,FORWARD_OPERATING_HORIZON_REQUESTS,RECURRENCE_WILSON_Z
from .contracts import PUBLIC_OPERATIONAL_CONTRACT_VERSION,public_operational_contract_manifest

def write_jsonl(path,rows):
    with open(path,"w",encoding="utf8") as f:
        for r in rows:f.write(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n")
def _hash_json(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def summarize(rows):
    investments=[x for x in rows if x["route"] in ("reason_and_promote","relearn_and_promote")]
    wasted=[]
    for inv in investments:
        reused=any(y["sequence"]>inv["sequence"] and y["family"]==inv["family"] and y["version"]==inv["version"] and y["route"]=="deterministic_reuse" for y in rows)
        if not reused:wasted.append(inv)
    return {"requests":len(rows),"correct":sum(x["correct"] for x in rows),"accuracy":sum(x["correct"] for x in rows)/len(rows),"llm_calls":sum(x["llm_called"] for x in rows),"input_tokens":sum(x["input_tokens"] for x in rows),"output_tokens":sum(x["output_tokens"] for x in rows),"total_tokens":sum(x["input_tokens"]+x["output_tokens"] for x in rows),"provider_cost_micro":sum(x["provider_cost_micro"] for x in rows),"optimization_overhead_micro":sum(x["optimization_overhead_micro"] for x in rows),"lifetime_benchmark_cost_micro":sum(x["provider_cost_micro"]+x["optimization_overhead_micro"] for x in rows),"deterministic_reuses":sum(x["route"]=="deterministic_reuse" for x in rows),"stale_reuse_errors":sum((not x["correct"]) and x["stale_reuse"] for x in rows),"optimization_investments":len(investments),"wasted_optimization_investments":len(wasted),"wasted_optimization_cost_micro":sum(x["optimization_overhead_micro"] for x in wasted)}

def run(provider_name="mock",mode="canonical",output_dir=None):
    workload=build()
    if mode=="demo":workload=[workload[i-1] for i in [1,2,3,4,5,6,25,40,70,91,100,121,140,160,180]]
    run_id="ch12-"+datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+uuid.uuid4().hex[:8]
    out=Path(output_dir or ("evidence/demo-real-v1" if mode=="demo" else "evidence/benchmark-real-v1" if provider_name!="mock" else "evidence/mock-v1"));out.mkdir(parents=True,exist_ok=True)
    provider=make_provider(provider_name);archs=[AlwaysReason(provider),AlwaysOptimize(provider),SmartSelective(provider)];ledgers={}
    for a in archs:
        rows=[a.handle(r) for r in workload];ledgers[a.name]=rows;write_jsonl(out/f"{a.name}_ledger.jsonl",rows)
        if isinstance(a,SmartSelective):write_jsonl(out/"optimization_cases.jsonl",a.case_events);write_jsonl(out/"capability_events.jsonl",a.capability_events)
    write_jsonl(out/"workload.jsonl",[r.public_dict() for r in workload]);write_jsonl(out/"ground_truth.jsonl",[{"request_id":r.request_id,**asdict(ground_truth(r))} for r in workload])
    summary={k:summarize(v) for k,v in ledgers.items()}
    cost_profiles=cost_profiles_dict();policy={"min_observations":MIN_OBSERVATIONS,"safety_margin_micro":SAFETY_MARGIN_MICRO,"forward_operating_horizon_requests":FORWARD_OPERATING_HORIZON_REQUESTS,"recurrence_estimator":"wilson_lower_bound","recurrence_wilson_z":RECURRENCE_WILSON_Z}
    provider_contract=public_operational_contract_manifest()
    manifest={"run_id":run_id,"mode":mode,"provider":provider_name,"model":getattr(provider,"model","unknown"),"python":platform.python_version(),"platform":platform.platform(),"request_count":len(workload),"canonical_workload_hash":workload_hash(build()),"input_usd_per_million":INPUT_USD_PER_MILLION,"output_usd_per_million":OUTPUT_USD_PER_MILLION,"policy_version":"chapter12-v1.0.3","policy_hash":_hash_json(policy),"cost_manifest_hash":_hash_json(cost_profiles),"provider_contract_version":PUBLIC_OPERATIONAL_CONTRACT_VERSION,"provider_contract_hash":_hash_json(provider_contract)}
    cost_manifest={"provider_pricing":{"input_usd_per_million":INPUT_USD_PER_MILLION,"output_usd_per_million":OUTPUT_USD_PER_MILLION},"assigned_cost_profiles":cost_profiles,"policy":policy,"note":"Optimization overhead values are frozen benchmark-assigned accounting assumptions, not market prices. Promotion/relearning overhead includes acquisition or relearning + validation + declared maintenance."}
    for name,obj in [("manifest.json",manifest),("summary.json",summary),("cost_manifest.json",cost_manifest)]:(out/name).write_text(json.dumps(obj,indent=2,sort_keys=True),encoding="utf8")
    return manifest,summary,out

