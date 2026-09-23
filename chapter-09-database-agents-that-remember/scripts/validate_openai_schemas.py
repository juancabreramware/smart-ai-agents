from _common import ROOT
from src.planner.schemas import OUTPUT_SCHEMA
assert OUTPUT_SCHEMA['type']=='object' and OUTPUT_SCHEMA.get('additionalProperties') is False
for k,v in OUTPUT_SCHEMA['properties'].items(): assert 'type' in v
assert set(OUTPUT_SCHEMA['required'])==set(OUTPUT_SCHEMA['properties'])
print('PASS chapter9_query_capability')
print('Validated strict Structured Outputs schema locally. No API call was made.')
