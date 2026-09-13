from __future__ import annotations
import json
from pathlib import Path
from integration.schema import stable_hash
ROOT=Path(__file__).resolve().parents[1]

def load_contract(version:int)->dict:
    return json.loads((ROOT/'contracts'/f'contract_v{version}.json').read_text())

def op_contract(contract:dict, api:str, operation:str)->dict:
    return contract['apis'][api][operation]

def dependency(api:str, operation:str)->str: return f'{api}:{operation}'

def schema_hash(contract:dict, api:str, operation:str, side:str)->str:
    spec=op_contract(contract,api,operation)
    if side=='request':
        return stable_hash({'required':spec.get('required',[]),'conditional':spec.get('conditional',{}),'scope':spec.get('scope')})
    return stable_hash(spec.get('response',[]))
