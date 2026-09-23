from pathlib import Path
from src.workload import build,workload_hash
from src.contracts import drifted_families,get_contract
from src.models import Candidate,Request
from src.capabilities import validate,promote,ALLOWED
from src.provider import payload,MockProvider
from src.agents import Smart
from src.runner import run
from src.audit import audit
def test_workload():
    w=build(150);assert len(w)==150 and len({x.request_id for x in w})==150 and sum(x.reasoning_required for x in w)==18 and sum(x.drift_event for x in w)==4 and len(workload_hash(w))==64
def test_selective_drift():assert drifted_families()=={"inventory_planning","invoice_escalation","supplier_scorecard","order_operations"}
def test_candidate():
    c=get_contract("inventory_planning","V1");x=Candidate(c.family,c.version,c.operation,list(c.dependencies),c.policy_fingerprint,c.environment_fingerprint);assert validate(x,c)[0];assert len(promote(x,c,1).implementation_hash)==64
def test_closed_allowlist():assert len(ALLOWED)==6 and "eval" not in ALLOWED and "exec" not in ALLOWED
def test_no_ground_truth_leak():
    r=Request("R",1,"shipment_sla","V1",{"eta_hours":30,"promised_hours":24},True,"note 1");s=str(payload(r,"x")).lower();assert "expected_action" not in s and "expected_value" not in s and "expected_label" not in s
def test_smart_routes():
    a=Smart(MockProvider());c={}
    for r in build(150):
        _,q,_,_,_,_=a.handle(r);c[q]=c.get(q,0)+1
    assert c=={"initial_acquisition":6,"reasoning_required":18,"relearning":4,"deterministic_reuse":122}
def test_mock(tmp_path:Path):
    m=run("canonical",MockProvider(),tmp_path);assert m["summaries"]["baseline"]["correct"]==150;assert m["summaries"]["smart"]["correct"]==150;assert m["summaries"]["smart"]["llm_calls"]==28;assert m["summaries"]["naive"]["llm_calls"]==24;assert m["summaries"]["naive"]["stale_reuse"]>=1;assert audit(tmp_path)["passed"]
