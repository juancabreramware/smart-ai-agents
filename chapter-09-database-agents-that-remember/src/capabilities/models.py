from dataclasses import dataclass,asdict
@dataclass
class QueryCapability:
    capability_id:str; capability_version:int; family_id:str; database_contract_version:str; sql_template:str; required_parameters:list; schema_fingerprint:str; status:str='validated'; provenance:dict=None
    def to_dict(self): return asdict(self)
