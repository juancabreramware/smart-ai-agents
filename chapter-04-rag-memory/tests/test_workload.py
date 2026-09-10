import json
from smart_agent.common import ROOT
def test_full_workload_shape():
    w=json.loads((ROOT/'workloads/full.json').read_text());assert len(w)==150;assert sum(x['source_version']=='v1' for x in w)==100;assert sum(x['source_version']=='v2' for x in w)==50
