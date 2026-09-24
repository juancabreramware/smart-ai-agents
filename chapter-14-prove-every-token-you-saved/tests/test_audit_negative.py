import json
from src.provider import MockProvider
from src.runner import run
from scripts.audit_evidence import audit
def lines(p): return [x for x in p.read_text().splitlines() if x.strip()]
def test_auditor_catches_deleted_attempt(tmp_path):
    run(MockProvider(),tmp_path,40,"test")
    p=tmp_path/"provider_attempts.jsonl"; x=lines(p); p.write_text("\n".join(x[:-1])+"\n")
    a=audit(tmp_path); assert not a["passed"]
def test_auditor_catches_duplicate_request(tmp_path):
    run(MockProvider(),tmp_path,40,"test")
    p=tmp_path/"workload.jsonl"; x=lines(p); p.write_text("\n".join(x+[x[0]])+"\n")
    a=audit(tmp_path); assert not a["passed"]
def test_auditor_catches_summary_edit(tmp_path):
    run(MockProvider(),tmp_path,40,"test")
    p=tmp_path/"evidence_grade_report.json"; d=json.loads(p.read_text()); d["provider_savings_micro"]+=1
    p.write_text(json.dumps(d))
    a=audit(tmp_path); assert not a["passed"] and any("summary mismatch" in e for e in a["errors"])
def test_auditor_catches_attempt_cost_tamper(tmp_path):
    run(MockProvider(),tmp_path,40,"test")
    p=tmp_path/"provider_attempts.jsonl"; x=[json.loads(v) for v in lines(p)]; x[0]["provider_cost_micro"]+=1
    p.write_text("\n".join(json.dumps(v) for v in x)+"\n")
    a=audit(tmp_path); assert not a["passed"] and any("attempt cost mismatch" in e for e in a["errors"])
