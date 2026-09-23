from pathlib import Path
import inspect
import src.architectures as architectures

def test_smart_production_decision_receives_global_sequence():
    source=inspect.getsource(architectures.SmartSelective.handle)
    assert "decide(case,r.family,r.sequence)" in source
    assert "decide(case,r.family)" not in source

def test_drift_path_has_economic_gate_before_relearning():
    source = inspect.getsource(architectures.SmartSelective.handle)

    # v1.0.3 invariant:
    # RELEARN must exist only behind an explicit PROMOTE decision.
    assert 'if case.decision=="PROMOTE"' in source
    assert '"event":"RELEARN"' in source

    promote_pos = source.find('if case.decision=="PROMOTE"')
    relearn_pos = source.find('"event":"RELEARN"')

    assert promote_pos >= 0
    assert relearn_pos > promote_pos

def test_execution_path_patch_does_not_modify_optimizer_source():
    source=Path("src/optimizer.py").read_text(encoding="utf8")
    assert "_future_reuse_estimate(case,sequence)" in source
    assert 'case.decision="DEFER"; case.decision_reason="BREAK_EVEN_NOT_YET_CLEARED"' in source
