from __future__ import annotations
import json,time,hashlib
from pathlib import Path
from src.database.fingerprints import schema_fingerprint
from src.validation.ground_truth import audit
from src.capabilities.registry import CapabilityRegistry
from src.agents.baseline import BaselineAgent
from src.agents.smart import SmartAgent
from src.agents.naive import NaiveAgent

def file_sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(workload,planner_factory,outdir,db_v1,db_v2):
    out=Path(outdir); out.mkdir(parents=True,exist_ok=True); summaries={}
    for arch in ['baseline','smart','naive']:
        planner=planner_factory(); registry=CapabilityRegistry(); current_version=None; agent=None; rows=[]
        for req in workload:
            db=db_v1 if req['contract_version']=='V1' else db_v2
            if current_version!=req['contract_version']:
                fp=schema_fingerprint(db)
                if agent is None:
                    agent=BaselineAgent(planner,db,fp) if arch=='baseline' else SmartAgent(planner,db,fp,registry) if arch=='smart' else NaiveAgent(planner,db,fp)
                else: agent.db_path=db; agent.schema_fp=fp
                current_version=req['contract_version']
            t=time.perf_counter(); err=None
            try: result=agent.process(req)
            except Exception as e:
                result={'routing_path':'error','llm_called':False,'sql_template':'','rows':[],'semantic_label':None,'runtime_validation':{'ok':False},'usage':{},'cost':0.0,'planner_latency_ms':0,'db_latency_ms':0,'capability_id':None,'capability_version':None,'compatibility_checks':{}}; err=f'{type(e).__name__}:{e}'
            elapsed=(time.perf_counter()-t)*1000; aud=audit(req['expected_result'],result['rows'],req.get('semantic_label') if req['reasoning_required'] else None,result.get('semantic_label'))
            stale=arch=='naive' and req['affected_by_drift'] and result['routing_path']=='naive_reuse' and not aud['ok']
            row={'request_id':req['request_id'],'architecture':arch,'phase':req['phase'],'query_family':req['query_family'],'database_contract_version':req['contract_version'],'database_snapshot_sha256':file_sha(db),'reasoning_required':req['reasoning_required'],'routing_path':result['routing_path'],'capability_id':result.get('capability_id'),'capability_version':result.get('capability_version'),'compatibility_checks':result.get('compatibility_checks',{}),'llm_called':result['llm_called'],'model':getattr(planner,'model','unknown'),'token_usage':result.get('usage',{}),'measured_llm_cost':result.get('cost',0.0),'parameter_values':req['parameters'],'sql_fingerprint':hashlib.sha256(result.get('sql_template','').encode()).hexdigest(),'runtime_validation':result.get('runtime_validation',{}),'audited_correct':aud['ok'],'component_accuracy':aud['component_accuracy'],'audit_reasons':aud['reasons'],'stale_reuse':stale,'latency_ms':{'end_to_end':elapsed,'planner':result.get('planner_latency_ms',0),'database':result.get('db_latency_ms',0)},'error':err}
            rows.append(row)
        (out/f'{arch}-executions.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows))
        summaries[arch]={'requests':len(rows),'correct':sum(r['audited_correct'] for r in rows),'llm_calls':sum(r['llm_called'] for r in rows),'cost':sum(r['measured_llm_cost'] for r in rows),'stale_incorrect':sum(r['stale_reuse'] for r in rows),'errors':sum(r['error'] is not None for r in rows)}
        if arch=='smart': registry.snapshot(out/'smart-capability-registry.json')
    (out/'execution-summary.json').write_text(json.dumps(summaries,indent=2)); return summaries
