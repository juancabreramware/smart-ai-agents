from __future__ import annotations
import argparse,json,hashlib,platform,sys,os
from pathlib import Path
from collections import Counter
from environment.simulator import EnterpriseApiSimulator
from integration.contracts import load_contract
from providers.planner import MockPlanner,OpenAIPlanner
from baseline.integration_agent import BaselineIntegrationAgent
from smart_agent.agent import SmartIntegrationAgent
from smart_agent.capability_registry import CapabilityRegistry
from naive_cache.agent import NaiveIntegrationCache
ROOT=Path(__file__).resolve().parents[1]

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_text())
def summary(rows):
    n=len(rows); calls=sum(r['llm_calls'] for r in rows); cost=sum(r['usage']['cost'] for r in rows); correct=sum(bool(r['audited_correct']) for r in rows)
    lats=sorted(r['latency_ms'] for r in rows)
    def pct(p): return lats[min(len(lats)-1,int(round((len(lats)-1)*p)))] if lats else 0
    return {'executions':n,'audited_correct':correct,'audited_correctness':correct/n if n else 0,'llm_calls':calls,'llm_avoidance':1-calls/n if n else 0,'cost':cost,'median_latency_ms':pct(.5),'p95_latency_ms':pct(.95),'paths':dict(Counter(r['path'] for r in rows)),'incorrect_stale_reuse':sum(bool(r.get('incorrect_stale_reuse')) for r in rows),'api_calls':sum(r.get('api_calls',0) for r in rows)}

def run_arch(name,requests,planner,outdir):
    env=EnterpriseApiSimulator(); reg=CapabilityRegistry() if name=='smart' else None
    agent=BaselineIntegrationAgent(planner) if name=='baseline' else SmartIntegrationAgent(planner,reg) if name=='smart' else NaiveIntegrationCache(planner)
    rows=[]; current=None; invalidated=[]
    for req in requests:
        v=int(req['contract_version']); contract=load_contract(v)
        if name=='smart' and current is not None and v!=current: invalidated.extend(agent.on_contract_change(contract))
        current=v; r=agent.handle(req,contract,env); r.update({'architecture':name,'request_id':req['request_id'],'phase':req['phase'],'contract_version':v,'request_class':req['request_class'],'operation_family':req['operation_family']}); rows.append(r)
    p=Path(outdir)/f'{name}.jsonl'; p.write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in rows))
    if name=='smart':
        (Path(outdir)/'smart_registry.json').write_text(json.dumps(reg.snapshot(),indent=2,sort_keys=True));
        (Path(outdir)/'smart_invalidated.json').write_text(json.dumps(invalidated,indent=2))
    return rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--mode',choices=['mock','real'],default='mock'); ap.add_argument('--workload',default=str(ROOT/'workloads'/'demo.json')); ap.add_argument('--architecture',choices=['all','baseline','smart','naive'],default='all'); ap.add_argument('--outdir',default=str(ROOT/'results'/'run'))
    a=ap.parse_args(); out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True); requests=load(a.workload)
    planner=MockPlanner() if a.mode=='mock' else OpenAIPlanner(); names=['baseline','smart','naive'] if a.architecture=='all' else [a.architecture]; sums={}
    for name in names: sums[name]=summary(run_arch(name,requests,planner,out))
    manifest={'mode':a.mode,'workload':str(Path(a.workload).resolve()),'workload_sha256':sha(a.workload),'model':'mock' if a.mode=='mock' else os.getenv('OPENAI_MODEL','gpt-5.6'),'python':sys.version,'platform':platform.platform(),'pricing':{'input_per_million':float(os.getenv('OPENAI_INPUT_PRICE_PER_MILLION','4')),'cached_input_per_million':float(os.getenv('OPENAI_CACHED_INPUT_PRICE_PER_MILLION','0.4')),'output_per_million':float(os.getenv('OPENAI_OUTPUT_PRICE_PER_MILLION','20'))}}
    (out/'summary.json').write_text(json.dumps(sums,indent=2)); (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(sums,indent=2))
if __name__=='__main__': main()
