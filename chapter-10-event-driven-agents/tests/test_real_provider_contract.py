from src.contracts import V1, V2, public_contract
from src.ground_truth import authoritative_decision
from src.provider import semantic_label_from_note, build_provider_payload, _parse_json_object
from src.workload import build_workload, workload_hash

EXPECTED_CANONICAL_HASH="eb4b617f26494106d8b63ee43463191ae5e3b2965b75175d0ed745f65538797e"

def _public_eval(obs):
    pc=public_contract(obs.family,obs.contract_version)
    if obs.reasoning_required:
        return "reasoning_action", semantic_label_from_note(obs.state["note"])
    r=pc["trigger_predicate"]
    s=obs.state
    t=pc["threshold"]
    if obs.family=="inventory_risk": triggered=float(s["available"]) < float(t)
    elif obs.family=="shipment_exception": triggered=float(s["eta_hours"]) > float(s["promised_hours"])
    elif obs.family=="order_sla": triggered=float(s["age_hours"]) > float(t)
    elif obs.family=="invoice_risk": triggered=float(s["days_overdue"]) > float(t)
    elif obs.family=="supplier_performance": triggered=float(s["score"]) < float(t)
    elif obs.family=="customer_account": triggered=float(s["risk_score"]) > float(t)
    else: raise AssertionError(obs.family)
    return ("deterministic_action" if triggered else "no_action"), None

def test_v102_preserves_canonical_workload_hash():
    assert workload_hash(build_workload())==EXPECTED_CANONICAL_HASH

def test_public_contracts_cover_all_six_families_and_v1_v2_tables():
    for requested_version,table in (("V1",V1),("V2",V2)):
        assert len(table)==6
        for family,c in table.items():
            p=public_contract(family,requested_version)
            assert p["family"]==family
            assert p["effective_contract_version"]==c.version
            assert p["semantic_version"]==c.semantic_version
            assert p["dependencies"]==list(c.dependencies)
            assert p["threshold"]==c.threshold
            assert p["unit"]==c.unit
            assert p["response_mode"]==c.response_mode
            assert p["trigger_predicate"]["operator"] in {"<",">"}

def test_public_contract_evaluation_matches_frozen_ground_truth_for_all_150():
    for obs in build_workload():
        action,label=_public_eval(obs)
        truth=authoritative_decision(obs)
        assert action==truth.action, obs.observation_id
        assert label==truth.label, obs.observation_id

def test_provider_payload_has_contract_but_never_hidden_answer_fields():
    for obs in build_workload():
        payload=build_provider_payload(obs,"test")
        assert "monitor_contract" in payload
        assert "trigger_predicate" in payload["monitor_contract"]
        assert "expected_action" not in payload
        assert "expected_label" not in payload
        assert "expected_action" not in str(payload)
        assert "expected_label" not in str(payload)

def test_reasoning_mapping_matches_all_frozen_reasoning_labels():
    reasoning=[o for o in build_workload() if o.reasoning_required]
    assert len(reasoning)==18
    for obs in reasoning:
        assert semantic_label_from_note(obs.state["note"])==obs.expected_label

def test_json_parser_accepts_plain_and_fenced_json():
    expected={"action":"no_action","label":None,"explanation":"ok"}
    assert _parse_json_object('{"action":"no_action","label":null,"explanation":"ok"}')==expected
    assert _parse_json_object('```json\n{"action":"no_action","label":null,"explanation":"ok"}\n```')==expected
