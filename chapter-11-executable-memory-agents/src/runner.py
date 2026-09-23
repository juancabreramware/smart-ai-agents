from datetime import datetime,timezone
import os,platform,sys,uuid
from .agents import Baseline,Smart,Naive
from .ground_truth import expected
from .workload import build,workload_hash
from .evidence import write_json,write_jsonl
def eq(a,b):
    try:
        if isinstance(a,float) or isinstance(b,float):return abs(float(a)-float(b))<1e-9
    except:pass
    return a==b
def run(mode,p,out):
    reqs=build(15 if mode=="demo" else 150);wh=workload_hash(reqs);rid=f"ch11-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    led={}
    for name,a in [("baseline",Baseline(p)),("naive",Naive(p)),("smart",Smart(p))]:
        rows=[]
        for r in reqs:
            e=expected(r);d,route,u,cap,compat,inv=a.handle(r);correct=d.action==e.action and eq(d.value,e.value) and d.label==e.label
            rows.append({"run_id":rid,"architecture":name,"request_id":r.request_id,"sequence":r.sequence,"family":r.family,"contract_version":r.contract_version,
            "route":route,"llm_call_count":1 if route in {"baseline_reasoning","initial_acquisition","reasoning_required","relearning"} else 0,"llm_called":route in {"baseline_reasoning","initial_acquisition","reasoning_required","relearning"},"input_tokens":u.input_tokens,"output_tokens":u.output_tokens,
            "measured_llm_cost_usd":u.cost_usd,"expected_action":e.action,"actual_action":d.action,"expected_value":e.value,"actual_value":d.value,"expected_label":e.label,"actual_label":d.label,
            "correct":correct,"stale_reuse":name=="naive" and r.contract_version=="V2" and route=="naive_reuse" and not correct,"compatibility":compat,"invalidated":inv,
            "capability_id":getattr(cap,"capability_id",None),"capability_version":getattr(cap,"capability_version",None),"implementation_hash":getattr(cap,"implementation_hash",None),
            "provider":p.name,"model":p.model,"workload_hash":wh})
        led[name]=rows;write_jsonl(out/f"{name}.jsonl",rows)
    sums={}
    for n,rows in led.items():
        calls=sum(x["llm_call_count"] for x in rows)
        sums[n]={"requests":len(rows),"correct":sum(x["correct"] for x in rows),"accuracy":sum(x["correct"] for x in rows)/len(rows),"llm_calls":calls,
        "llm_calls_avoided_vs_150":150-calls if mode=="canonical" else None,"input_tokens":sum(x["input_tokens"] for x in rows),"output_tokens":sum(x["output_tokens"] for x in rows),
        "measured_llm_cost_usd":round(sum(x["measured_llm_cost_usd"] for x in rows),10),"stale_reuse":sum(x["stale_reuse"] for x in rows),
        "routes":{k:sum(x["route"]==k for x in rows) for k in sorted({x["route"] for x in rows})}}
    m={"run_id":rid,"mode":mode,"provider":p.name,"model":p.model,"python":sys.version,"platform":platform.platform(),"workload_hash":wh,"request_count":len(reqs),
    "pricing":{"input_usd_per_million":os.getenv("CH11_INPUT_USD_PER_MILLION","0"),"output_usd_per_million":os.getenv("CH11_OUTPUT_USD_PER_MILLION","0")},"summaries":sums}
    write_json(out/"manifest.json",m);return m
