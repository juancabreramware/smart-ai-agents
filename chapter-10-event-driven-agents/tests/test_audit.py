from pathlib import Path
import os
from src.runner import run
from src.audit import audit

def test_mock_evidence_passes_independent_audit(tmp_path):
    os.environ["CH10_PROVIDER"]="mock"
    d=tmp_path/"evidence"
    run(d,demo=False)
    r=audit(d)
    assert r["passed"], r["errors"]
    assert r["recomputed"]["baseline"]["llm_calls"]==150
    assert r["recomputed"]["smart"]["llm_calls"]==28
    assert r["recomputed"]["naive"]["llm_calls"]==24
