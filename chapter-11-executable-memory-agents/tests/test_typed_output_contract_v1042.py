import pytest
from src.typed_values import normalize_typed_value,typed_equal,value_type_for_operation
from src.workload import build
from src.ground_truth import expected
from src.contracts import get_contract
from src.provider import normalize_decision,payload

def test_all_150_typed_contracts():
    w=build(150); assert len(w)==150
    for r in w:
        c=get_contract(r.family,r.contract_version); e=expected(r)
        kind=value_type_for_operation(c.operation)
        assert typed_equal(e.value,e.value,kind)
        assert payload(r,"produce_current_business_decision")["public_contract"]["value_type"]==kind

@pytest.mark.parametrize("v",[0,1,"0","1","false","true",None])
def test_boolean_rejects_non_boolean(v):
    with pytest.raises(ValueError): normalize_typed_value(v,"boolean")

def test_boolean_accepts_only_bool():
    assert normalize_typed_value(False,"boolean") is False
    assert normalize_typed_value(True,"boolean") is True

def test_numeric_serialization_equivalence():
    assert typed_equal("0",0,"integer")
    assert typed_equal("50",50,"integer")
    assert typed_equal("80.2",80.2,"number")

def test_boolean_zero_regression():
    r=next(x for x in build(150) if type(expected(x).value) is bool and expected(x).value is False)
    e=expected(r)
    with pytest.raises(ValueError,match="typed public contract"):
        normalize_decision({"action":e.action,"value":0,"label":e.label},r)

def test_all_six_operations_have_types():
    ops={get_contract(r.family,r.contract_version).operation for r in build(150)}
    assert len(ops)==6
    assert all(value_type_for_operation(op) in {"integer","boolean","number"} for op in ops)
