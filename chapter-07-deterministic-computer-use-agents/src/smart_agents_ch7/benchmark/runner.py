from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
import statistics
import time
from typing import Iterable

from smart_agents_ch7.agents.baseline import BaselineComputerUseAgent
from smart_agents_ch7.agents.smart import SmartComputerUseAgent
from smart_agents_ch7.agents.naive import NaiveReplayAgent
from smart_agents_ch7.benchmark.models import BenchmarkRequest
from smart_agents_ch7.benchmark.pricing import Pricing
from smart_agents_ch7.browser.executor import BrowserExecutor
from smart_agents_ch7.browser.simulated_executor import SimulatedBrowserExecutor
from smart_agents_ch7.capabilities.registry import CapabilityRegistry
from smart_agents_ch7.planner.mock import MockPlanner
from smart_agents_ch7.planner.openai_planner import OpenAIPlanner
from smart_agents_ch7.portal.contracts import contracts_for
from smart_agents_ch7.portal.server import PortalHarness
from smart_agents_ch7.portal.state import PortalState


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def planner_from_name(name: str):
    if name == "mock":
        return MockPlanner()
    if name == "openai":
        return OpenAIPlanner()
    raise ValueError(f"Unknown planner: {name}")


def _summary(records: list[dict]) -> dict:
    n = len(records)
    llm_calls = sum(1 for r in records if r["llm_called"])
    correct = sum(1 for r in records if r["audit"]["ok"])
    stale = sum(1 for r in records if r["stale_reuse"])
    cost = sum(float(r["measured_llm_cost"]) for r in records)
    routes: dict[str, int] = {}
    for r in records:
        routes[r["routing_path"]] = routes.get(r["routing_path"], 0) + 1
    latencies = [float(r.get("end_to_end_ms") or 0) for r in records]
    return {
        "requests": n,
        "correct": correct,
        "incorrect": n - correct,
        "correctness_pct": round((correct / n * 100) if n else 0.0, 4),
        "llm_calls": llm_calls,
        "llm_calls_avoided_vs_baseline_count": n - llm_calls,
        "llm_call_avoidance_pct": round(((n - llm_calls) / n * 100) if n else 0.0, 4),
        "measured_llm_cost_usd": round(cost, 10),
        "stale_incorrect_reuses": stale,
        "routing": routes,
        "latency_ms": {
            "median": round(statistics.median(latencies), 3) if latencies else 0.0,
            "p95": round(sorted(latencies)[max(0, int(0.95 * len(latencies)) - 1)], 3) if latencies else 0.0,
        },
    }


def run_architecture(
    architecture: str,
    requests: list[BenchmarkRequest],
    planner_name: str,
    output_path: Path,
    headless: bool = True,
    executor_name: str = "playwright",
) -> tuple[list[dict], list[dict] | None]:
    state = PortalState()
    planner = planner_from_name(planner_name)
    pricing = Pricing.from_env(getattr(planner, "model", "unknown"))
    registry = CapabilityRegistry() if architecture == "smart" else None

    records: list[dict] = []
    if executor_name == "simulated":
        harness = None
        browser_cm = SimulatedBrowserExecutor(state)
    elif executor_name == "playwright":
        harness = PortalHarness(state)
        harness.__enter__()
        browser_cm = BrowserExecutor(harness.base_url, headless=headless)
    else:
        raise ValueError(f"Unknown executor: {executor_name}")
    try:
        with browser_cm as browser:
            if architecture == "baseline":
                agent = BaselineComputerUseAgent(planner, browser, state, pricing)
            elif architecture == "smart":
                agent = SmartComputerUseAgent(planner, browser, state, pricing, registry=registry)
            elif architecture == "naive":
                agent = NaiveReplayAgent(planner, browser, state, pricing)
            else:
                raise ValueError(architecture)

            for req in requests:
                state.ui_version = req.ui_version
                contract = contracts_for(req.ui_version)[req.operation_family]
                started = time.perf_counter()
                outcome = agent.handle(req, contract)
                outcome.end_to_end_ms = (time.perf_counter() - started) * 1000
                record = {
                    "request": req.to_dict(),
                    **outcome.to_dict(),
                    "ui_contract": {
                        "family_contract_version": contract.family_contract_version,
                        "fingerprint": contract.fingerprint(),
                    },
                }
                records.append(record)

    finally:
        if harness is not None:
            harness.__exit__(None, None, None)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, sort_keys=True) + "\n")

    registry_snapshot = registry.snapshot() if registry else None
    return records, registry_snapshot


def run_suite(
    requests: list[BenchmarkRequest],
    planner_name: str,
    output_dir: Path,
    workload_path: Path | None = None,
    headless: bool = True,
    executor_name: str = "playwright",
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    all_summaries = {}
    smart_registry = None

    for architecture in ("baseline", "smart", "naive"):
        records, registry = run_architecture(
            architecture,
            requests,
            planner_name,
            output_dir / f"{architecture}-executions.jsonl",
            headless=headless,
            executor_name=executor_name,
        )
        all_summaries[architecture] = _summary(records)
        if architecture == "smart":
            smart_registry = registry

    if smart_registry is not None:
        (output_dir / "smart-capability-registry.json").write_text(
            json.dumps(smart_registry, indent=2, sort_keys=True), encoding="utf-8"
        )

    planner = planner_from_name(planner_name)
    pricing = Pricing.from_env(getattr(planner, "model", "unknown"))
    manifest = {
        "schema_version": 1,
        "chapter": 7,
        "experiment_specification": "v1.0",
        "planner": planner_name,
        "model": getattr(planner, "model", "unknown"),
        "pricing": pricing.to_dict(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "request_count_per_architecture": len(requests),
        "architectures": ["baseline", "smart", "naive"],
        "executor": executor_name,
        "workload_sha256": sha256_file(workload_path) if workload_path and workload_path.exists() else None,
        "canonical": False,
        "note": "Mock/local outputs are validation evidence only. Set canonical only after the real benchmark is reviewed and frozen.",
    }
    (output_dir / "experiment-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    summary = {
        "schema_version": 1,
        "architectures": all_summaries,
    }
    baseline_cost = all_summaries["baseline"]["measured_llm_cost_usd"]
    for name in ("smart", "naive"):
        cost = all_summaries[name]["measured_llm_cost_usd"]
        savings = baseline_cost - cost
        summary["architectures"][name]["measured_llm_savings_vs_baseline_usd"] = round(savings, 10)
        summary["architectures"][name]["measured_llm_cost_reduction_pct"] = round((savings / baseline_cost * 100), 4) if baseline_cost else 0.0
    (output_dir / "execution-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary
