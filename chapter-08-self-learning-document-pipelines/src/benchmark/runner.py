from __future__ import annotations
import hashlib,json,time
from pathlib import Path
from src.documents.parser import extract_text
from src.validation.ground_truth import audit
from src.capabilities.registry import CapabilityRegistry
from src.agents.baseline import BaselineAgent
from src.agents.smart import SmartAgent
from src.agents.naive import NaiveAgent

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def run(workload,planner_factory,outdir):
    out=Path(outdir); out.mkdir(parents=True,exist_ok=True); root=Path(__file__).resolve().parents[2]
    summaries={}
    for arch in ['baseline','smart','naive']:
        planner=planner_factory(); registry=CapabilityRegistry()
        agent=BaselineAgent(planner) if arch=='baseline' else SmartAgent(planner,registry) if arch=='smart' else NaiveAgent(planner)
        rows=[]
        for req in workload:
            path=root/req['document_path']; text=extract_text(path); t=time.perf_counter()
            try: result=agent.process(text,req); err=None
            except Exception as e:
                result={'routing_path':'error','llm_called':False,'fields':{},'semantic_label':None,'runtime_validation':{'ok':False},'usage':{},'cost':0.0,'capability_id':None,'capability_version':None,'compatibility_checks':{}}; err=f'{type(e).__name__}:{e}'
            elapsed=(time.perf_counter()-t)*1000
            aud=audit(req['expected_fields'],result['fields'],req.get('semantic_label') if req['reasoning_required'] else None,result.get('semantic_label'))
            stale=arch=='naive' and req['contract_version']=='V2' and req['affected_by_drift'] and result['routing_path']=='naive_reuse' and not aud['ok']
            row={'request_id':req['request_id'],'architecture':arch,'phase':req['phase'],'document_path':req['document_path'],'document_sha256':sha(path),'family_id':req['family_id'],'family_contract_version':req['contract_version'],'reasoning_required':req['reasoning_required'],'routing_path':result['routing_path'],'capability_id':result.get('capability_id'),'capability_version':result.get('capability_version'),'compatibility_checks':result.get('compatibility_checks',{}),'llm_called':result['llm_called'],'model':getattr(planner,'model','unknown'),'token_usage':result.get('usage',{}),'measured_llm_cost':result.get('cost',0.0),'extracted_fields':result['fields'],'semantic_label':result.get('semantic_label'),'runtime_validation':result.get('runtime_validation',{}),'audited_correct':aud['ok'],'field_accuracy':aud['field_accuracy'],'audit_reasons':aud['reasons'],'stale_reuse':stale,'latency_ms':{'end_to_end':elapsed,'planner':result.get('planner_latency_ms',0)},'error':err}
            rows.append(row)
        (out/f'{arch}-executions.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows))
        summaries[arch]={'requests':len(rows),'correct':sum(r['audited_correct'] for r in rows),'llm_calls':sum(r['llm_called'] for r in rows),'cost':sum(r['measured_llm_cost'] for r in rows),'stale_incorrect':sum(r['stale_reuse'] for r in rows),'errors':sum(r['error'] is not None for r in rows)}
        if arch=='smart': registry.snapshot(out/'smart-capability-registry.json')
    (out/'execution-summary.json').write_text(json.dumps(summaries,indent=2)); return summaries
