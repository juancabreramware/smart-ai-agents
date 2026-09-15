from pathlib import Path

from smart_agents_ch7.benchmark.audit import audit_directory
from smart_agents_ch7.benchmark.runner import run_suite
from smart_agents_ch7.benchmark.workload import build_demo


def test_independent_audit_recomputes_raw_ledgers(tmp_path: Path):
    run_suite(build_demo(), "mock", tmp_path, executor_name="simulated")
    report = audit_directory(tmp_path)
    assert report["identical_request_ids_and_order"] is True
    assert report["passes_basic_integrity"] is True
    assert report["architectures"]["smart"]["correct"] == 15
