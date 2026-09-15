from pathlib import Path

from smart_agents_ch7.benchmark.runner import run_suite
from smart_agents_ch7.benchmark.workload import build_demo


def test_demo_exposes_safe_reuse_and_naive_staleness(tmp_path: Path):
    summary = run_suite(build_demo(), "mock", tmp_path, executor_name="simulated")
    assert summary["architectures"]["baseline"]["correct"] == 15
    assert summary["architectures"]["smart"]["correct"] == 15
    assert summary["architectures"]["smart"]["stale_incorrect_reuses"] == 0
    assert summary["architectures"]["naive"]["stale_incorrect_reuses"] == 4
    assert summary["architectures"]["naive"]["incorrect"] == 4
