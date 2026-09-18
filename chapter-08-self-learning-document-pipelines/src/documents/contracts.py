from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load_contract(version:str)->dict:
    return json.loads((ROOT/'contracts'/f'document-contract-{version.lower()}.json').read_text())
def required_fields(family:str, version:str)->list[str]:
    return load_contract(version)['families'][family]['required_fields']
