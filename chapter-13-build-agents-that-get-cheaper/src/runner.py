from __future__ import annotations
import hashlib,json,platform,uuid
from pathlib import Path
from dataclasses import asdict
from .workload import build,workload_hash,public_record,WORKLOAD_VERSION
from .scoring import ground_truth
from .provider import make_provider
from .architectures import StatelessReason,EpisodicReuse,CompoundingSmart
from .accounting import provider_cost_micro,INPUT_USD_PER_MILLION,OUTPUT_USD_PER_MILLION
from .contracts import CONTRACT_VERSION,contract_manifest,hash_json
from .capabilities import POLICY_VERSION,POLICY_HASH

def _summary(rows):
    requests=len(rows); correct=sum(x["correct"] for x in rows)
    inp=sum(x["input_tokens"] for x in rows); out=sum(x["output_tokens"] for x in rows)
    calls=sum(x["llm_called"] for x in rows); reuse=sum(x["route"]=="deterministic_reuse" for x in rows)
    stale=sum(x["stale_reuse_error"] for x in rows)
    return {"requests":requests,"correct":correct,"accuracy":correct/requests if requests else 0,
            "llm_calls":calls,"input_tokens":inp,"output_tokens":out,"total_tokens":inp+out,
            "provider_cost_micro":provider_cost_micro(inp,out),"deterministic_reuses":reuse,
            "stale_reuse_errors":stale,"llm_calls_per_request":calls/requests if requests else 0,
            "tokens_per_request":(inp+out)/requests if requests else 0,
            "provider_cost_micro_per_request":provider_cost_micro(inp,out)/requests if requests else 0}

def run(output_dir:str,provider_name="mock",mode="canonical",request_limit:int|None=None):
    canonical=build(); workload=canonical if request_limit is None else canonical[:request_limit]
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    provider=make_provider(provider_name)
    archs=[StatelessReason(provider),EpisodicReuse(provider),CompoundingSmart(provider)]
    all_rows={}; all_events={}
    for arch in archs:
        rows=[]; last_wave=None
        for r in workload:
            if r.wave!=last_wave:
                arch.on_wave_start(r.wave); last_wave=r.wave
            ans,usage,route,capid=arch.handle(r)
            gt=ground_truth(r)
            inp=usage.input_tokens if usage else 0; outtok=usage.output_tokens if usage else 0
            correct=ans.value==gt.value
            rows.append({
                **public_record(r),"architecture":arch.name,"route":route,"capability_id":capid,
                "answer":ans.value,"expected":gt.value,"correct":correct,
                "llm_called":usage is not None,"input_tokens":inp,"output_tokens":outtok,
                "provider_cost_micro":provider_cost_micro(inp,outtok),
                "stale_reuse_error":route=="deterministic_reuse" and not correct,
            })
        all_rows[arch.name]=rows; all_events[arch.name]=arch.events
        with (out/f"{arch.name}_ledger.jsonl").open("w",encoding="utf-8") as f:
            for x in rows: f.write(json.dumps(x,sort_keys=True)+"\n")
        with (out/f"{arch.name}_capability_events.jsonl").open("w",encoding="utf-8") as f:
            for x in arch.events: f.write(json.dumps(x,sort_keys=True)+"\n")

    with (out/"workload.jsonl").open("w",encoding="utf-8") as f:
        for r in workload: f.write(json.dumps(public_record(r),sort_keys=True)+"\n")
    with (out/"ground_truth.jsonl").open("w",encoding="utf-8") as f:
        for r in workload: f.write(json.dumps({"request_id":r.request_id,"expected":ground_truth(r).value},sort_keys=True)+"\n")

    summary={name:_summary(rows) for name,rows in all_rows.items()}
    wave_summary={}
    for name,rows in all_rows.items():
        wave_summary[name]={str(w):_summary([x for x in rows if x["wave"]==w]) for w in sorted(set(x["wave"] for x in rows))}

    manifest={
        "run_id":"ch13-"+uuid.uuid4().hex[:12],"mode":mode,"provider":provider_name,
        "model":getattr(provider,"model","unknown"),"python":platform.python_version(),"platform":platform.platform(),
        "request_count":len(workload),"canonical_request_count":len(canonical),
        "canonical_workload_hash":workload_hash(canonical),"workload_version":WORKLOAD_VERSION,
        "input_usd_per_million":INPUT_USD_PER_MILLION,"output_usd_per_million":OUTPUT_USD_PER_MILLION,
        "policy_version":POLICY_VERSION,"policy_hash":POLICY_HASH,
        "public_contract_version":CONTRACT_VERSION,"public_contract_hash":hash_json(contract_manifest()),
    }
    for name,obj in [("manifest.json",manifest),("summary.json",summary),("wave_summary.json",wave_summary)]:
        (out/name).write_text(json.dumps(obj,indent=2,sort_keys=True),encoding="utf-8")
    return {"manifest":manifest,"summary":summary,"wave_summary":wave_summary,"output_dir":str(out)}
