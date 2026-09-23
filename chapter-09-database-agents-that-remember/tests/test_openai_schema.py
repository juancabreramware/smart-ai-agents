from src.planner.schemas import OUTPUT_SCHEMA
def test_strict_schema():
    assert OUTPUT_SCHEMA['additionalProperties'] is False
    assert set(OUTPUT_SCHEMA['required'])==set(OUTPUT_SCHEMA['properties'])
    assert all('type' in v for v in OUTPUT_SCHEMA['properties'].values())
