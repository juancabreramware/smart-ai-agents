from src.workload import build_workload
from src.runtime import execute
from src.scoring import truth
from src.contracts import public_contract
def test_runtime_matches_independent_truth_for_frozen_workload():
    for r in build_workload(240):
        assert execute(r,public_contract(r.family,r.contract_version)["operation"]) == truth(r)
def test_runtime_source_has_no_scoring_dependency():
    from pathlib import Path
    s=(Path(__file__).resolve().parents[1]/"src/runtime.py").read_text()
    assert "scoring" not in s and "truth(" not in s
def test_openai_provider_source_has_no_hidden_scoring_dependency():
    from pathlib import Path
    s=(Path(__file__).resolve().parents[1]/"src/provider.py").read_text()
    assert "scoring" not in s and "truth(" not in s and "failure_mode" not in s
