from __future__ import annotations
from pydantic import BaseModel, ConfigDict
class ExecutableDocumentCapability(BaseModel):
    model_config=ConfigDict(extra='forbid')
    capability_id:str
    capability_version:int
    family_id:str
    family_contract_version:str
    required_fields:list[str]
    fingerprint:str
    validation_status:str='validated'
    provenance:dict={}
