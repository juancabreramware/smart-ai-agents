import pytest
from src.provider import payload, normalize_decision, OPERATION_SEMANTICS
from src.models import Request
from src.contracts import get_contract
from src.capabilities import execute

def _r(family,version,inputs):
    return Request("REG",1,family,version,inputs,False,None)

def test_inventory_prompt_exposes_exact_semantics():
    r=_r("inventory_planning","V1",{"on_hand":100,"reserved":10,"reorder_point":50,"target_stock":140})
    p=payload(r,"produce_current_business_decision")
    s=p["public_contract"]["executable_semantics"]
    assert s==OPERATION_SEMANTICS["inventory_reorder"]
    assert "available = on_hand - reserved" in s["steps"]
    assert "available < trigger_level" in s["steps"][2]

def test_regression_model_cannot_place_order_when_public_rule_says_no_action():
    # Regression for the real-demo failure: model returned place_order/value=50
    # while the trusted public-contract executor returned no_action.
    r=_r("inventory_planning","V1",{"on_hand":100,"reserved":10,"reorder_point":50,"target_stock":140})
    c=get_contract(r.family,r.contract_version)
    expected=execute(c.operation,r.inputs,c,None)
    assert expected.action=="no_action"
    with pytest.raises(ValueError,match="conflicts"):
        normalize_decision({"action":"place_order","value":50,"label":None},r)

def test_matching_inventory_decision_passes():
    r=_r("inventory_planning","V1",{"on_hand":100,"reserved":10,"reorder_point":50,"target_stock":140})
    c=get_contract(r.family,r.contract_version)
    d=execute(c.operation,r.inputs,c,None)
    assert normalize_decision({"action":d.action,"value":d.value,"label":None},r)=={
        "action":d.action,"value":d.value,"label":None
    }

def test_all_contract_operations_have_public_semantics():
    cases=[
        ("inventory_planning","V1",{"on_hand":1,"reserved":0,"reorder_point":5,"target_stock":10}),
        ("shipment_sla","V1",{"eta_hours":30,"promised_hours":24}),
        ("invoice_escalation","V1",{"days_overdue":10,"amount":2000}),
        ("supplier_scorecard","V1",{"on_time_rate":90,"quality_rate":90}),
        ("customer_account","V1",{"balance":2000,"days_overdue":10}),
        ("order_operations","V1",{"age_hours":40})
    ]
    for family,version,inputs in cases:
        p=payload(_r(family,version,inputs),"produce_current_business_decision")
        assert p["public_contract"]["operation"] in OPERATION_SEMANTICS
        assert p["public_contract"]["executable_semantics"]["steps"]
