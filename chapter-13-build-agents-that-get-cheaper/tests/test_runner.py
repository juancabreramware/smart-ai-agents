import json
from pathlib import Path
from src.runner import run
def test_mock_runner_and_wave_metrics(tmp_path):
    result=run(str(tmp_path),"mock","test")
    assert result["manifest"]["request_count"]==240
    assert set(result["wave_summary"]["compounding_smart"])=={"1","2","3","4"}
    assert result["summary"]["stateless_reason"]["llm_calls"]==240
    assert result["summary"]["compounding_smart"]["deterministic_reuses"]>0
def test_all_mock_correct(tmp_path):
    r=run(str(tmp_path),"mock","test")
    assert all(v["correct"]==240 for v in r["summary"].values())
def test_compounding_later_wave_call_rate_falls_in_mock(tmp_path):
    r=run(str(tmp_path),"mock","test")
    waves=r["wave_summary"]["compounding_smart"]
    assert waves["2"]["llm_calls_per_request"] < waves["1"]["llm_calls_per_request"]
