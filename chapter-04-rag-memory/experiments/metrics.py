from __future__ import annotations
import statistics

def summarize(results):
    n=len(results); lat=[x.latency_ms for x in results]; costs=[x.cost_usd for x in results]
    def pct(v,p):
        if not v:return 0
        s=sorted(v); return s[min(len(s)-1,max(0,int(round((len(s)-1)*p))))]
    usages=[x.usage for x in results]
    paths={}
    events={}
    for x in results:
        paths[x.path]=paths.get(x.path,0)+1
        for e in x.events:events[e]=events.get(e,0)+1
    llm=sum(u.get('llm_calls',0) for u in usages)
    return {'executions':n,'successful':sum(x.correct for x in results),'correctness':sum(x.correct for x in results)/n if n else 0,
      'routing_policy_correctness':sum(x.routing_correct for x in results)/n if n else 0,'llm_calls':llm,
      'input_tokens':sum(u.get('input_tokens',0) for u in usages),'cached_input_tokens':sum(u.get('cached_input_tokens',0) for u in usages),'output_tokens':sum(u.get('output_tokens',0) for u in usages),
      'embedding_calls':sum(u.get('embedding_calls',0) for u in usages),'embedding_tokens':sum(u.get('embedding_tokens',0) for u in usages),
      'total_cost_usd':sum(costs),'median_latency_ms':statistics.median(lat) if lat else 0,'p95_latency_ms':pct(lat,.95),
      'memory_reuse_rate':paths.get('MEMORY',0)/n if n else 0,'llm_avoidance_rate':1-llm/n if n else 0,'fallback_rate':paths.get('RELEARNING',0)/n if n else 0,
      'memory_lookups':events.get('MEMORY_LOOKUP',0),'memory_hits':events.get('MEMORY_VALID',0)+events.get('MEMORY_INVALIDATED',0),'memory_misses':events.get('MEMORY_MISS',0),'document_retrievals':events.get('RETRIEVE',0)+events.get('ACQUIRE',0)+events.get('REASONING_REQUIRED',0)+events.get('MEMORY_INVALIDATED',0),'memory_invalidations':events.get('MEMORY_INVALIDATED',0),'memory_promotions':events.get('MEMORY_PROMOTED',0),'incorrect_stale_reuse':sum(x.stale_reuse for x in results),
      'paths':paths,'events':events}
