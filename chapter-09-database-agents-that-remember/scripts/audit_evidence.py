import argparse,json,sys
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('evidence'); p.add_argument('--expected-count',type=int,default=150); a=p.parse_args(); d=Path(a.evidence); rows={}
for arch in ['baseline','smart','naive']:
    f=d/f'{arch}-executions.jsonl'; rows[arch]=[json.loads(x) for x in f.read_text().splitlines() if x.strip()]
ids=[[r['request_id'] for r in rows[x]] for x in rows]; snaps=[[r['database_snapshot_sha256'] for r in rows[x]] for x in rows]
report={'identical_request_ids_order':ids[0]==ids[1]==ids[2],'identical_database_snapshots':snaps[0]==snaps[1]==snaps[2],'architectures':{}}
for k,rs in rows.items(): report['architectures'][k]={'requests':len(rs),'correct':sum(r['audited_correct'] for r in rs),'incorrect':sum(not r['audited_correct'] for r in rs),'component_accuracy':sum(r['component_accuracy'] for r in rs)/len(rs),'llm_calls':sum(r['llm_called'] for r in rs),'cost':sum(r['measured_llm_cost'] for r in rs),'stale_incorrect':sum(r['stale_reuse'] for r in rs),'routing':{x:sum(r['routing_path']==x for r in rs) for x in sorted(set(r['routing_path'] for r in rs))}}
report['passes_basic_integrity']=report['identical_request_ids_order'] and report['identical_database_snapshots'] and all(len(x)==a.expected_count for x in rows.values())
(d/'audit-report.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2)); sys.exit(0 if report['passes_basic_integrity'] else 2)
