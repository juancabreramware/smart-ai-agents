from pathlib import Path
import json
from src.capabilities.models import ExecutableDocumentCapability
from src.capabilities.compatibility import fingerprint,compatible
from src.capabilities.compiler import deterministic_extract
from src.validation.runtime import validate
ROOT=Path(__file__).resolve().parents[1]
def test_contracts_have_six_families():
    for v in ['v1','v2']:
        x=json.loads((ROOT/'contracts'/f'document-contract-{v}.json').read_text()); assert len(x['families'])==6
def test_capability_is_strict():
    s=ExecutableDocumentCapability.model_json_schema(); assert s.get('additionalProperties') is False
def test_fingerprint_detects_structural_drift(): assert fingerprint('A: 1\nB: 2') != fingerprint('A: 1\nC: 2')
def test_extract_and_validate():
    f=deterministic_extract('A: 1\nB: 2',['a','b']); assert f=={'a':'1','b':'2'}; assert validate(f,['a','b'])['ok']
def test_changed_family_contract_flags():
    v2=json.loads((ROOT/'contracts'/'document-contract-v2.json').read_text()); assert sum(x['changed_from_v1'] for x in v2['families'].values())==4
