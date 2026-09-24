from src.provider import MockProvider
from src.runner import run
from scripts.audit_evidence import audit
def test_mock_run_and_audit(tmp_path):
    r=run(MockProvider(),tmp_path,240,"test")
    assert r["evidence_grade_report.json"]["request_count"]==240
    a=audit(tmp_path); assert a["passed"],a["errors"]
def test_smart_reuses(tmp_path):
    r=run(MockProvider(),tmp_path,240,"test")
    assert r["evidence_grade_report.json"]["deterministic_reuses"]>0
def test_naive_overstatement_is_computable(tmp_path):
    r=run(MockProvider(),tmp_path,240,"test")
    assert "savings_overstatement_micro" in r["evidence_grade_report.json"]
