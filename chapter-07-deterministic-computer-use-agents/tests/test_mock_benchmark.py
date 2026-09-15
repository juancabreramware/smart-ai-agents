from pathlib import Path

from smart_agents_ch7.benchmark.runner import run_suite
from smart_agents_ch7.benchmark.workload import build_benchmark


def test_mock_benchmark_architecture_shape(tmp_path: Path):
    summary = run_suite(build_benchmark(), "mock", tmp_path, executor_name="simulated")
    b = summary["architectures"]["baseline"]
    s = summary["architectures"]["smart"]
    n = summary["architectures"]["naive"]
    assert (b["correct"], b["llm_calls"]) == (150, 150)
    assert s["correct"] == 150
    assert s["stale_incorrect_reuses"] == 0
    assert s["routing"] == {
        "INITIAL_ACQUISITION": 6,
        "DETERMINISTIC_REUSE": 122,
        "REASONING_REQUIRED": 18,
        "RELEARNING": 4,
    }
    assert n["correct"] == 118
    assert n["stale_incorrect_reuses"] == 32
