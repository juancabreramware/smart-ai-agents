"""One-command controlled experiment for Chapter 3.

This runner starts the local benchmark site, compares both architectures on v1,
changes the page structure to v2, compares both again, and writes a full ledger/report.
"""
from __future__ import annotations

# Allow this file to be executed directly as `python experiments/<script>.py`
# without requiring the project to be installed as a package first.
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import subprocess
import time

import requests
import yaml

from benchmark.report import generate_report
from experiments.helpers import controlled_task, ground_truth
from experiments.inject_failure import set_version
from smart_agent.baseline_agent import BaselineAgent
from smart_agent.model_provider import provider_from_name
from smart_agent.registry import CapabilityRegistry
from smart_agent.settings import settings
from smart_agent.smart_agent import SmartPricingAgent
from smart_agent.telemetry import LedgerWriter, write_manifest

ROOT = Path(__file__).resolve().parents[1]


def wait_for_site(base_url: str, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    health = base_url.rstrip("/") + "/health"
    while time.time() < deadline:
        try:
            if requests.get(health, timeout=0.5).ok:
                return
        except requests.RequestException:
            pass
        time.sleep(0.1)
    raise RuntimeError("Controlled benchmark site did not become healthy in time")


def run_phase(*, version: str, count: int, phase: str, task, baseline: BaselineAgent, smart: SmartPricingAgent, ledger: LedgerWriter, pause: float) -> None:
    truth = ground_truth(version)
    for i in range(1, count + 1):
        print(f"\n[{phase}] execution {i}/{count}")

        _, b = baseline.run(
            task=task, experiment_id=ledger.experiment_id, phase=phase,
            ground_truth_path=truth
        )
        ledger.append(b)
        print(
            f"  baseline path={b.path.value:<13} model_calls={b.model.calls:<2} "
            f"score={b.correctness_score:.3f} cost=${b.total_cost_usd:.6f}"
        )

        _, s = smart.run(
            task=task, experiment_id=ledger.experiment_id, phase=phase,
            ground_truth_path=truth
        )
        ledger.append(s)
        print(
            f"  smart    path={s.path.value:<13} model_calls={s.model.calls:<2} "
            f"cap=v{s.capability_version or '-'} score={s.correctness_score:.3f} "
            f"cost=${s.total_cost_usd:.6f}"
        )
        if s.fallback_occurred:
            print(f"           -> fallback/relearning: {s.fallback_reason}")

        # Book code should teach while it runs. If a candidate is rejected, surface the
        # reason here instead of making readers spelunk through executions.jsonl.
        if not s.validation_passed and s.notes:
            error_notes = [note for note in s.notes if note.startswith("ERROR:")]
            for note in (error_notes or s.notes[-2:]):
                print(f"           -> {note}")

        if pause:
            time.sleep(pause)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--provider", default="openai", choices=["openai", "mock"])
    p.add_argument("--config", default="config/experiment.demo.yaml")
    p.add_argument("--reset", action="store_true")
    args = p.parse_args()

    config = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))
    experiment_id = config["experiment_id"]
    provider = provider_from_name(args.provider)
    registry = CapabilityRegistry()
    ledger = LedgerWriter(experiment_id)

    if args.reset:
        registry.reset()
        ledger.reset()
        out = settings.ledger_dir / experiment_id
        if out.exists():
            for name in [
                "summary.md", "summary.json", "cumulative_cost.png",
                "llm_calls_by_execution.png", "latency_by_architecture.png",
                "manifest.json",
            ]:
                path = out / name
                if path.exists():
                    path.unlink()

    initial = config["controlled_site"]["initial_version"]
    changed = config["controlled_site"]["changed_version"]
    set_version(initial)

    host = str(config["controlled_site"]["host"])
    port = int(config["controlled_site"]["port"])
    server = subprocess.Popen(
        [sys.executable, "-u", str(ROOT / "benchmark_site" / "server.py"), "--host", host, "--port", str(port)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        wait_for_site(f"http://{host}:{port}")
        write_manifest(experiment_id, provider.name, provider.model_name, config)
        baseline = BaselineAgent(provider)
        smart = SmartPricingAgent(provider, registry)

        run_phase(
            version=initial,
            count=int(config["v1_executions"]),
            phase="V1_STABLE",
            task=controlled_task(host, port),
            baseline=baseline,
            smart=smart,
            ledger=ledger,
            pause=float(config.get("pause_seconds", 0)),
        )

        print("\n" + "=" * 72)
        print("BREAKING THE ENVIRONMENT: switching controlled site to v2")
        print("=" * 72)
        set_version(changed)
        time.sleep(0.25)

        run_phase(
            version=changed,
            count=int(config["v2_executions"]),
            phase="V2_AFTER_CHANGE",
            task=controlled_task(host, port),
            baseline=baseline,
            smart=smart,
            ledger=ledger,
            pause=float(config.get("pause_seconds", 0)),
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()

    report = generate_report(experiment_id)
    print("\n" + "=" * 72)
    print("EXPERIMENT COMPLETE")
    print("=" * 72)
    print(f"Ledger:       {ledger.path}")
    print(f"Report:       {report}")
    print(f"Capabilities: {registry.root}")


if __name__ == "__main__":
    main()
