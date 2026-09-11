from __future__ import annotations
import argparse, json, os, statistics, time
from pathlib import Path
from environment.simulator import EnterpriseEnvironment
from providers.planner import MockPlanner, OpenAIPlanner
from baseline.planning_agent import BaselinePlanningAgent
from smart_agent.agent import SmartWorkflowAgent
from smart_agent.capability_registry import CapabilityRegistry
from naive_cache.plan_cache import NaivePlanCacheAgent
from workflows.ground_truth import expected_ops

ROOT=Path(__file__).resolve().parents[1]

def load_json(path): return json.loads(Path(path).read_text())
def pricing():
    # Intentionally configurable: freeze verified prices in evidence at benchmark time.
    return {
      "input_per_million":float(os.getenv("PRICE_INPUT_PER_MILLION","4.0")),
      "cached_input_per_million":float(os.getenv("PRICE_CACHED_INPUT_PER_MILLION","0.4")),
      "output_per_million":float(os.getenv("PRICE_OUTPUT_PER_MILLION","20.0"))
    }
def cost(usage,p):
    inp=usage.get("input_tokens",0); cached=usage.get("cached_input_tokens",0); out=usage.get("output_tokens",0)
    uncached=max(0,inp-cached)
    return uncached/1e6*p["input_per_million"] + cached/1e6*p["cached_input_per_million"] + out/1e6*p["output_per_million"]

def run_architecture(name, requests, mode="mock", outdir=None):
    p1=load_json(ROOT/"policies/policy_v1.json"); p2=load_json(ROOT/"policies/policy_v2.json")
    planner=MockPlanner() if mode=="mock" else OpenAIPlanner()
    reg=CapabilityRegistry()
    if name=="baseline": agent=BaselinePlanningAgent(planner)
    elif name=="smart": agent=SmartWorkflowAgent(planner,reg)
    elif name=="naive": agent=NaivePlanCacheAgent(planner)
    else: raise ValueError(name)
    env=EnterpriseEnvironment(p1); rows=[]; current_version=1
    for req in requests:
        desired=req["policy_version"]
        if desired!=current_version:
            current_version=desired; env.policy=p2
            if name=="smart":
                invalidated=reg.invalidate_changed(p2["changed_dependencies"])
            else: invalidated=[]
        else: invalidated=[]
        policy=p1 if desired==1 else p2
        env.seed_for_request(req)
        result=agent.handle(req,policy,env)
        # independent operation-sequence audit
        actual=[x["op"] for x in result.get("plan",{}).get("steps",[])]
        expected=expected_ops(req,policy)
        semantic_ok=(actual==expected and result.get("ok",False))
        usage=result.get("usage",{})
        row={"request_id":req["request_id"],"policy_version":desired,"architecture":name,
             "workflow_family":req["workflow_family"],"result":result,
             "expected_ops":expected,"actual_ops":actual,"audited_correct":semantic_ok,
             "invalidated_on_transition":invalidated,"cost":cost(usage,pricing())}
        rows.append(row)
    if outdir:
        Path(outdir).mkdir(parents=True,exist_ok=True)
        (Path(outdir)/f"{name}.jsonl").write_text("\n".join(json.dumps(x,sort_keys=True) for x in rows))
        if name=="smart": (Path(outdir)/"smart_registry.json").write_text(json.dumps(reg.dump(),indent=2))
    return rows

def summarize(rows):
    lats=[r["result"]["latency_ms"] for r in rows]
    llm=sum(r["result"].get("llm_calls",0) for r in rows)
    n=len(rows)
    return {
      "executions":n,
      "audited_correct":sum(r["audited_correct"] for r in rows),
      "audited_correctness":sum(r["audited_correct"] for r in rows)/n,
      "llm_calls":llm,
      "llm_avoidance":1-llm/n,
      "cost":sum(r["cost"] for r in rows),
      "median_latency_ms":statistics.median(lats),
      "p95_latency_ms":sorted(lats)[max(0,int(.95*n)-1)],
      "paths":{p:sum(r["result"].get("path")==p for r in rows) for p in sorted(set(r["result"].get("path") for r in rows))},
      "incorrect_stale_reuse":sum(bool(r["result"].get("incorrect_stale_reuse")) for r in rows)
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--architecture",choices=["baseline","smart","naive","all"],default="all")
    ap.add_argument("--workload",default=str(ROOT/"workloads/demo.json"))
    ap.add_argument("--mode",choices=["mock","real"],default="mock")
    ap.add_argument("--outdir",default=str(ROOT/"results/latest"))
    args=ap.parse_args()
    reqs=load_json(args.workload)
    names=["baseline","smart","naive"] if args.architecture=="all" else [args.architecture]
    summary={}
    for name in names:
        rows=run_architecture(name,reqs,args.mode,args.outdir)
        summary[name]=summarize(rows)
    Path(args.outdir).mkdir(parents=True,exist_ok=True)
    (Path(args.outdir)/"summary.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))

if __name__=="__main__": main()
