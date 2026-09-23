from _common import ROOT
from src.database.seed import build
build(ROOT/'workloads'/'harborpoint-v1.sqlite',ROOT/'schema'/'schema-v1.sql')
build(ROOT/'workloads'/'harborpoint-v2.sqlite',ROOT/'schema'/'schema-v2.sql')
from src.benchmark.generate import generate
rows,demo=generate(ROOT/'workloads'/'harborpoint-v1.sqlite',ROOT/'workloads'/'harborpoint-v2.sqlite')
import json
(ROOT/'workloads'/'benchmark_v1.0.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows))
(ROOT/'workloads'/'demo_v1.0.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in demo))
(ROOT/'workloads'/'ground-truth.jsonl').write_text(''.join(json.dumps({'request_id':r['request_id'],'expected_result':r['expected_result'],'semantic_label':r['semantic_label']},separators=(',',':'))+'\n' for r in rows))
print('Built V1/V2 databases, 150-request benchmark, 15-request demo, and ground truth.')
