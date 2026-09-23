from src.provider import OPERATION_SEMANTICS
def test_v10511_inventory_keeps_intermediate_semantics_and_correct_action_value():
    s=OPERATION_SEMANTICS["inventory_reorder"]
    assert s["steps"]==["available = on_hand - reserved","trigger_level = reorder_point + safety_buffer","triggered = available < trigger_level","if triggered: action = reorder","otherwise: action = no_action"]
    assert s["value_rule"]=={"reorder":"order_quantity","no_action":"0"}
