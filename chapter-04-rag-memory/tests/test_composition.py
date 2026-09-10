import json
from smart_agent.common import ROOT
from smart_agent.agent import SmartAgent
from smart_agent.settings import Settings
def test_composition_v2_ground_truth():
    r=next(x for x in json.loads((ROOT/'workloads/full.json').read_text()) if x['source_version']=='v2' and x['canonical_intent']=='enterprise_support_in_eu')
    x=SmartAgent(Settings(provider='mock',embeddings='local')).run(r);assert x.correct;assert x.answer['regions']==['Frankfurt','Dublin']
