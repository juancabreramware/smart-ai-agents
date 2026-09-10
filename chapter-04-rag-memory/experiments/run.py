from __future__ import annotations
import argparse,csv,json,platform,sys,time
from pathlib import Path
from baseline.rag_agent import BaselineRAGAgent
from smart_agent.agent import SmartAgent
from naive_cache.semantic_cache import NaiveSemanticCache
from smart_agent.common import ROOT
from smart_agent.settings import Settings
from .metrics import summarize
from .economics import economics

def run_arch(agent,workload,label,verbose=False):
    out=[]
    for r in workload:
        x=agent.run(r);out.append(x)
        if verbose: print(f"{label:11} {x.query_id} {x.source_version} {x.path:14} correct={x.correct} llm={x.usage.get('llm_calls',0)} events={','.join(x.events)}")
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['demo','full'],default='demo');ap.add_argument('--architectures',default='baseline,smart,naive_cache');ap.add_argument('--verbose',action='store_true');args=ap.parse_args()
    s=Settings(); workload=json.loads((ROOT/'workloads'/f'{args.mode}.json').read_text()); dest=ROOT/'results'/f"{args.mode}-{time.strftime('%Y%m%d-%H%M%S')}";dest.mkdir(parents=True,exist_ok=True)
    agents={'baseline':BaselineRAGAgent(s),'smart':SmartAgent(s),'naive_cache':NaiveSemanticCache(s)}; allres={}; summaries={}
    for name in args.architectures.split(','):
        name=name.strip(); res=run_arch(agents[name],workload,name,args.verbose or args.mode=='demo');allres[name]=res;summaries[name]=summarize(res)
    econ=economics(summaries['baseline'],summaries['smart']) if 'baseline' in summaries and 'smart' in summaries else {}
    manifest={'mode':args.mode,'provider':s.provider,'embeddings':s.embeddings,'model':s.model,'embedding_model':s.embedding_model,'python':platform.python_version(),'workload_count':len(workload),'pricing':{'input_per_m':s.input_per_m,'cached_input_per_m':s.cached_input_per_m,'output_per_m':s.output_per_m,'embedding_per_m':s.embedding_per_m}}
    (dest/'run_manifest.json').write_text(json.dumps(manifest,indent=2));(dest/'summary.json').write_text(json.dumps(summaries,indent=2));(dest/'economics.json').write_text(json.dumps(econ,indent=2))
    with (dest/'execution_ledger.jsonl').open('w') as f:
        for name,res in allres.items():
            for x in res:f.write(json.dumps(x.to_dict())+'\n')
    with (dest/'benchmark_results.csv').open('w',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=['architecture','query_id','source_version','canonical_intent','path','correct','routing_correct','latency_ms','cost_usd','stale_reuse']);wr.writeheader()
        for res in allres.values():
            for x in res:wr.writerow({k:getattr(x,k) for k in wr.fieldnames})
    stale={'naive_cache_incorrect_stale_reuse':summaries.get('naive_cache',{}).get('incorrect_stale_reuse',0),'smart_incorrect_stale_reuse':summaries.get('smart',{}).get('incorrect_stale_reuse',0),'smart_invalidations':summaries.get('smart',{}).get('memory_invalidations',0)}
    memory_events=[]
    for x in allres.get('smart',[]):
        for e in x.events:
            if e.startswith('MEMORY_') or e in ('SOURCE_CHANGED','ACQUIRE','VALIDATED'):
                memory_events.append({'query_id':x.query_id,'source_version':x.source_version,'intent':x.canonical_intent,'event':e,'path':x.path})
    with (dest/'memory_events.jsonl').open('w') as f:
        for e in memory_events:f.write(json.dumps(e)+'\n')
    (dest/'stale_memory_report.json').write_text(json.dumps(stale,indent=2));(dest/'routing_breakdown.json').write_text(json.dumps({k:v['paths'] for k,v in summaries.items()},indent=2));(dest/'token_cost_summary.json').write_text(json.dumps({k:{x:v[x] for x in ['llm_calls','input_tokens','cached_input_tokens','output_tokens','embedding_calls','embedding_tokens','total_cost_usd']} for k,v in summaries.items()},indent=2));(dest/'latency_summary.json').write_text(json.dumps({k:{'median_latency_ms':v['median_latency_ms'],'p95_latency_ms':v['p95_latency_ms']} for k,v in summaries.items()},indent=2))
    md=['# Chapter 4 Benchmark Summary','',f"Mode: {args.mode}",f"Provider: {s.provider}",f"Embeddings: {s.embeddings}",'']
    for k,v in summaries.items():md += [f'## {k}',f"- Correctness: {v['correctness']:.3f}",f"- LLM calls: {v['llm_calls']}",f"- Memory reuse rate: {v['memory_reuse_rate']:.1%}",f"- LLM avoidance: {v['llm_avoidance_rate']:.1%}",f"- Incorrect stale reuse: {v['incorrect_stale_reuse']}",f"- Total measured configured cost: ${v['total_cost_usd']:.6f}",'']
    (dest/'summary.md').write_text('\n'.join(md)); print('\nRESULTS:',dest);print(json.dumps(summaries,indent=2));return 0 if all(v['correctness']==1 for k,v in summaries.items() if k!='naive_cache') else 2
if __name__=='__main__':raise SystemExit(main())
