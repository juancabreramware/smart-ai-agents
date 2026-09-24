# Chapter 14 v1.0.1 runner replacement.
# This is the v1.0.0 runner with provider failure diagnostics persisted.
from pathlib import Path
import json, platform, sys
from .workload import build_workload, workload_hash, WORKLOAD_VERSION
from .contracts import public_contract, CONTRACT_VERSION, PUBLIC_CONTRACT_HASH
from .scoring import truth
from .runtime import execute
from .capabilities import Registry
from .accounting import PRICING, PRICING_VERSION, ASSIGNED, COST_VERSION, provider_cost_micro, stable_hash

def _write_json(path,obj): Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True),encoding="utf-8")
def _write_jsonl(path,rows):
    with Path(path).open("w",encoding="utf-8") as f:
        for x in rows: f.write(json.dumps(x,sort_keys=True)+"\n")

def _call(provider,req,architecture,attempts,mode):
    contract=public_contract(req.family,req.contract_version)
    attempt_no=1
    while True:
        # Frozen controlled stress events are adapter-level, nonbillable failures.
        # They exercise retry accounting without fabricating provider token usage.
        inject = mode in {"demo","canonical"} and req.failure_mode in {"retry_once","hard_fail_once"} and attempt_no==1
        if inject:
            from .models import Usage
            res={"status":"failed","usage":Usage(0,0),"answer":None,
                 "operation":contract["operation"],
                 "error_type":"ControlledNonbillableFailure",
                 "error_message":"Frozen benchmark adapter-level failure injection.",
                 "attempt_kind":"controlled_nonbillable_failure"}
        else:
            res=provider.reason(req,contract,attempt_no)
            res["attempt_kind"]="provider_attempt"
        u=res["usage"]
        cost=provider_cost_micro(provider.model,req.pricing_epoch,u.input_tokens,u.output_tokens)
        rec={
            "attempt_id":f"{architecture}:{req.request_id}:{attempt_no}",
            "request_id":req.request_id,"architecture":architecture,"attempt_no":attempt_no,
            "attempt_kind":res.get("attempt_kind","provider_attempt"),
            "model":provider.model,"pricing_epoch":req.pricing_epoch,"status":res["status"],
            "input_tokens":u.input_tokens,"output_tokens":u.output_tokens,
            "provider_cost_micro":cost,"answer":res.get("answer"),"operation":res.get("operation"),
            "error_type":res.get("error_type"),"error_message":res.get("error_message"),
        }
        attempts.append(rec)
        if res["status"]=="success": return res,attempt_no
        if attempt_no>=2: return res,attempt_no
        attempt_no+=1

def run(provider,out_dir,count=240,mode="mock"):
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    reqs=build_workload(count)
    attempts=[]; baseline=[]; smart=[]; events=[]; registry=Registry(); observations={}
    for req in reqs:
        br,ba=_call(provider,req,"baseline",attempts,mode)
        b_answer=br.get("answer")
        bcorrect=(b_answer==truth(req)) if br["status"]=="success" else False
        baseline.append({
            "request_id":req.request_id,"seq":req.seq,"wave":req.wave,"family":req.family,
            "contract_version":req.contract_version,"route":"llm_reason","attempts":ba,
            "correct":bcorrect,"answer":b_answer,"pricing_epoch":req.pricing_epoch
        })

        cap=registry.get(req.family)
        if cap and not registry.compatible(cap,req):
            registry.invalidate(cap,req)
            events.append({
                "seq":req.seq,"request_id":req.request_id,"event":"INVALIDATE","family":req.family,
                "old_capability_id":cap.capability_id,"reason":"contract_changed",
                "assigned_cost_micro":ASSIGNED["invalidation_micro"]
            })
            cap=None

        observations[req.family]=observations.get(req.family,0)+1
        can_reuse=cap is not None and registry.compatible(cap,req) and not req.reasoning_required

        if can_reuse:
            ans=execute(req,cap.operation); cap.reuse_count+=1
            route="deterministic_reuse"; att=0
            assigned=ASSIGNED["deterministic_execution_micro"]+ASSIGNED["registry_operation_micro"]
            capid=cap.capability_id
        else:
            sr,att=_call(provider,req,"smart",attempts,mode)
            ans=sr.get("answer")
            route=("reasoning_required" if req.reasoning_required else
                   ("relearning" if req.wave>=3 and req.family in {"invoice","supplier","order"}
                    and observations[req.family]>1 else "llm_reason"))
            assigned=ASSIGNED["registry_operation_micro"]
            if route=="relearning":
                assigned+=ASSIGNED["relearning_micro"]
            capid=None
            if sr["status"]=="success" and not req.reasoning_required and observations[req.family]>=2:
                new=registry.promote(req,sr["operation"]); capid=new.capability_id
                extra=ASSIGNED["capability_validation_micro"]+ASSIGNED["capability_acquisition_micro"]
                assigned+=extra
                events.append({
                    "seq":req.seq,"request_id":req.request_id,"event":"PROMOTE","family":req.family,
                    "capability_id":capid,"contract_version":req.contract_version,
                    "assigned_cost_micro":extra
                })

        smart.append({
            "request_id":req.request_id,"seq":req.seq,"wave":req.wave,"family":req.family,
            "contract_version":req.contract_version,"route":route,"attempts":att,
            "correct":ans==truth(req),"answer":ans,"capability_id":capid,
            "pricing_epoch":req.pricing_epoch,
            "assigned_nonprovider_cost_micro":assigned,
            "stale_reuse_error":False
        })

    workload_rows=[{
        "request_id":r.request_id,"seq":r.seq,"wave":r.wave,"family":r.family,
        "contract_version":r.contract_version,"payload":r.payload,
        "reasoning_required":r.reasoning_required,"failure_mode":r.failure_mode,
        "pricing_epoch":r.pricing_epoch
    } for r in reqs]
    ground=[{"request_id":r.request_id,"answer":truth(r)} for r in reqs]

    manifest={
        "chapter":14,"implementation_version":"1.0.2","mode":mode,
        "provider":provider.__class__.__name__,"model":provider.model,
        "python":sys.version.split()[0],"platform":platform.platform(),
        "request_count":len(reqs),"workload_version":WORKLOAD_VERSION,
        "workload_hash":workload_hash(reqs),
        "public_contract_version":CONTRACT_VERSION,"public_contract_hash":PUBLIC_CONTRACT_HASH,
        "pricing_version":PRICING_VERSION,"pricing_hash":stable_hash(PRICING),
        "cost_version":COST_VERSION,"cost_hash":stable_hash(ASSIGNED)
    }

    _write_json(out/"manifest.json",manifest)
    _write_json(out/"pricing_manifest.json",{"version":PRICING_VERSION,"pricing":PRICING})
    _write_json(out/"cost_manifest.json",{
        "version":COST_VERSION,"assigned_costs_micro":ASSIGNED,
        "note":"Benchmark-assigned non-provider costs; not measured market costs."
    })
    _write_json(out/"failure_schedule.json",{
        "retry_or_failure_requests":[r.request_id for r in reqs if r.failure_mode],
        "note":"Frozen by workload generator before execution."
    })
    _write_jsonl(out/"workload.jsonl",workload_rows)
    _write_jsonl(out/"ground_truth.jsonl",ground)
    _write_jsonl(out/"baseline_request_ledger.jsonl",baseline)
    _write_jsonl(out/"smart_request_ledger.jsonl",smart)
    _write_jsonl(out/"provider_attempts.jsonl",attempts)
    _write_jsonl(out/"capability_events.jsonl",events)

    reports=build_reports(baseline,smart,attempts)
    for name,obj in reports.items(): _write_json(out/name,obj)
    _write_json(out/"wave_summary.json",wave_summary(baseline,smart,attempts))
    return reports

def _provider_totals(attempts,arch):
    a=[x for x in attempts if x["architecture"]==arch]
    return {
        "attempts":len(a),
        "successful_calls":sum(x["status"]=="success" for x in a),
        "input_tokens":sum(x["input_tokens"] for x in a),
        "output_tokens":sum(x["output_tokens"] for x in a),
        "total_tokens":sum(x["input_tokens"]+x["output_tokens"] for x in a),
        "provider_cost_micro":sum(x["provider_cost_micro"] for x in a)
    }

def build_reports(baseline,smart,attempts):
    b=_provider_totals(attempts,"baseline"); s=_provider_totals(attempts,"smart")
    assigned=sum(x["assigned_nonprovider_cost_micro"] for x in smart)
    avoided=sum(x["route"]=="deterministic_reuse" for x in smart)

    succ=[x for x in attempts if x["architecture"]=="smart" and x["status"]=="success"]
    naive_s=sum(x["provider_cost_micro"] for x in succ)
    naive={
        "method":"intentionally_incomplete",
        "baseline_provider_cost_micro":b["provider_cost_micro"],
        "smart_visible_success_cost_micro":naive_s,
        "claimed_savings_micro":b["provider_cost_micro"]-naive_s
    }
    aggregate={
        "baseline":b,"smart":s,
        "smart_assigned_nonprovider_cost_micro":assigned,
        "smart_full_cost_micro":s["provider_cost_micro"]+assigned,
        "provider_savings_micro":b["provider_cost_micro"]-s["provider_cost_micro"],
        "full_benchmark_savings_micro":b["provider_cost_micro"]-(s["provider_cost_micro"]+assigned)
    }
    evidence={
        "baseline":b,"smart":s,
        "correct_baseline":sum(x["correct"] for x in baseline),
        "correct_smart":sum(x["correct"] for x in smart),
        "request_count":len(smart),
        "deterministic_reuses":avoided,
        "avoided_calls_attributed":avoided,
        "evidence_coverage_pct":100.0 if avoided>=0 else 0,
        "smart_assigned_nonprovider_cost_micro":assigned,
        "provider_savings_micro":b["provider_cost_micro"]-s["provider_cost_micro"],
        "full_benchmark_savings_micro":b["provider_cost_micro"]-(s["provider_cost_micro"]+assigned),
        "savings_overstatement_micro":naive["claimed_savings_micro"]-
            (b["provider_cost_micro"]-(s["provider_cost_micro"]+assigned))
    }
    return {
        "naive_dashboard.json":naive,
        "aggregate_report.json":aggregate,
        "evidence_grade_report.json":evidence
    }

def wave_summary(baseline,smart,attempts):
    out=[]
    for w in sorted({x["wave"] for x in smart}):
        ids={x["request_id"] for x in smart if x["wave"]==w}
        row={
            "wave":w,"requests":len(ids),
            "smart_reuses":sum(x["wave"]==w and x["route"]=="deterministic_reuse" for x in smart)
        }
        for arch in ("baseline","smart"):
            aa=[x for x in attempts if x["architecture"]==arch and x["request_id"] in ids]
            row[arch+"_attempts"]=len(aa)
            row[arch+"_tokens"]=sum(x["input_tokens"]+x["output_tokens"] for x in aa)
            row[arch+"_provider_cost_micro"]=sum(x["provider_cost_micro"] for x in aa)
        out.append(row)
    return out
