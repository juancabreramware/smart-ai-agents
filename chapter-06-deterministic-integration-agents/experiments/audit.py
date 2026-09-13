from __future__ import annotations
import argparse,json,hashlib
from pathlib import Path

def rows(path): return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('directory'); a=ap.parse_args(); d=Path(a.directory)
    report={}
    for name in ['baseline','smart','naive']:
        p=d/f'{name}.jsonl'
        if not p.exists(): continue
        rs=rows(p); report[name]={'rows':len(rs),'correct':sum(x['audited_correct'] for x in rs),'llm_calls':sum(x['llm_calls'] for x in rs),'cost':sum(x['usage']['cost'] for x in rs),'stale':sum(bool(x.get('incorrect_stale_reuse')) for x in rs)}
    if (d/'smart_registry.json').exists(): report['smart_registry_sha256']=hashlib.sha256((d/'smart_registry.json').read_bytes()).hexdigest()
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()
