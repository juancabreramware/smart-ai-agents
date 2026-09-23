import pytest
from types import SimpleNamespace
from src.provider import _strict_response_schema,_parse_strict_response,payload
from src.workload import build
from src.ground_truth import expected
def test_acquisition_schema_is_strict_closed():
    f=_strict_response_schema(payload(build(150)[0],"acquire_or_relearn_capability"))
    assert f["type"]=="json_schema" and f["strict"] is True
    assert f["schema"]["additionalProperties"] is False
    assert set(f["schema"]["required"])==set(f["schema"]["properties"])
def test_all_150_decision_schemas_match_ground_truth_types():
    for r in build(150):
        f=_strict_response_schema(payload(r,"produce_current_business_decision"))
        assert f["strict"] is True and f["schema"]["additionalProperties"] is False
        v=expected(r).value
        typ="boolean" if type(v) is bool else "integer" if type(v) is int else "number"
        assert f["schema"]["properties"]["value"]["type"]==typ
def test_strict_parser_accepts_completed_json_object():
    assert _parse_strict_response(SimpleNamespace(status="completed",output_text='{"x":1}',incomplete_details=None))=={"x":1}
@pytest.mark.parametrize("status",["incomplete","failed","cancelled",None])
def test_strict_parser_rejects_noncompleted(status):
    with pytest.raises(ValueError,match="did not complete"):
        _parse_strict_response(SimpleNamespace(status=status,output_text='{"x":1}',incomplete_details={"reason":"test"}))
def test_strict_parser_rejects_non_json_without_recovery():
    with pytest.raises(ValueError,match="not valid JSON"):
        _parse_strict_response(SimpleNamespace(status="completed",output_text='prefix {"x":1} suffix',incomplete_details=None))
def test_strict_parser_rejects_non_object():
    with pytest.raises(ValueError,match="JSON object"):
        _parse_strict_response(SimpleNamespace(status="completed",output_text='[1,2]',incomplete_details=None))
def test_unknown_task_fails_closed():
    with pytest.raises(ValueError,match="No strict response schema"):_strict_response_schema({"task":"unexpected"})
