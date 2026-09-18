from __future__ import annotations
from src.capabilities.compiler import deterministic_extract
from src.documents.contracts import required_fields
class MockPlanner:
    model='mock-planner'
    def extract(self,text,family,version,reasoning_required=False,expected=None):
        fields=deterministic_extract(text,required_fields(family,version),family,version)
        label=(expected or {}).get('semantic_label') if reasoning_required else None
        return {'family_id':family,'fields':fields,'semantic_label':label,'usage':{'input_tokens':0,'output_tokens':0,'cached_input_tokens':0,'reasoning_tokens':0},'cost':0.0,'response_id':'mock'}
