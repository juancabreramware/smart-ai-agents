"""Turn the raw JSONL execution ledger into tables and reproducible charts."""
from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

from smart_agent.models import ExecutionLedgerEntry
from smart_agent.settings import settings


def load_entries(experiment_id: str) -> list[ExecutionLedgerEntry]:
    path = settings.ledger_dir / experiment_id / "executions.jsonl"
    return [
        ExecutionLedgerEntry.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _stats(rows: list[ExecutionLedgerEntry]) -> dict:
    latencies = [r.latency_ms for r in rows]
    scores = [r.correctness_score for r in rows if r.correctness_score is not None]
    return {
        "executions": len(rows),
        "successes": sum(r.result == "SUCCESS" for r in rows),
        "correctness_mean": statistics.mean(scores) if scores else 0.0,
        "model_calls": sum(r.model.calls for r in rows),
        "input_tokens": sum(r.model.input_tokens for r in rows),
        "cached_input_tokens": sum(r.model.cached_input_tokens for r in rows),
        "output_tokens": sum(r.model.output_tokens for r in rows),
        "search_calls": sum(r.tools.search_calls for r in rows),
        "http_calls": sum(r.tools.http_calls for r in rows),
        "browser_calls": sum(r.tools.browser_calls for r in rows),
        "total_cost_usd": sum(r.total_cost_usd for r in rows),
        "median_latency_ms": statistics.median(latencies) if latencies else 0.0,
        "p95_latency_ms": sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)] if latencies else 0.0,
        "fallbacks": sum(r.fallback_occurred for r in rows),
        "llm_avoidance_rate": sum(r.model.calls == 0 for r in rows) / len(rows) if rows else 0.0,
    }


def generate_report(experiment_id: str) -> Path:
    rows = load_entries(experiment_id)
    out = settings.ledger_dir / experiment_id
    baseline_rows = [r for r in rows if r.architecture.value == "BASELINE"]
    smart_rows = [r for r in rows if r.architecture.value == "SMART"]
    b, s = _stats(baseline_rows), _stats(smart_rows)

    acquisition_rows = [r for r in smart_rows if r.path.value == "REASONING"]
    relearn_rows = [r for r in smart_rows if r.path.value == "RELEARNING"]
    det_rows = [r for r in smart_rows if r.path.value == "DETERMINISTIC"]
    acquisition_cost = acquisition_rows[0].total_cost_usd if acquisition_rows else 0.0
    relearning_cost = sum(r.total_cost_usd for r in relearn_rows)
    baseline_avg = statistics.mean(r.total_cost_usd for r in baseline_rows) if baseline_rows else 0.0
    deterministic_avg = statistics.mean(r.total_cost_usd for r in det_rows) if det_rows else 0.0
    savings_per_reuse = baseline_avg - deterministic_avg
    break_even = acquisition_cost / savings_per_reuse if acquisition_cost > 0 and savings_per_reuse > 0 else None

    summary = {
        "experiment_id": experiment_id,
        "baseline": b,
        "smart": s,
        "capability_acquisition_cost_usd": acquisition_cost,
        "relearning_cost_usd": relearning_cost,
        "baseline_avg_cost_usd": baseline_avg,
        "smart_deterministic_avg_cost_usd": deterministic_avg,
        "measured_savings_usd": b["total_cost_usd"] - s["total_cost_usd"],
        "break_even_execution_estimate": break_even,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    break_even_text = f"{break_even:.2f} reused executions" if break_even is not None else "not computable from configured/measured costs"
    md = (
        f"# Chapter 3 Benchmark Report — {experiment_id}\n\n"
        "> **Measured data only unless explicitly labeled as an estimate.** Costs are only meaningful if current pricing was configured before the run.\n\n"
        "| Metric | Baseline | Smart |\n|---|---:|---:|\n"
        f"| Executions | {b['executions']} | {s['executions']} |\n"
        f"| Successful executions | {b['successes']} | {s['successes']} |\n"
        f"| Mean correctness | {b['correctness_mean']:.3f} | {s['correctness_mean']:.3f} |\n"
        f"| LLM calls | {b['model_calls']} | {s['model_calls']} |\n"
        f"| Input tokens | {b['input_tokens']} | {s['input_tokens']} |\n"
        f"| Cached input tokens | {b['cached_input_tokens']} | {s['cached_input_tokens']} |\n"
        f"| Output tokens | {b['output_tokens']} | {s['output_tokens']} |\n"
        f"| Search calls | {b['search_calls']} | {s['search_calls']} |\n"
        f"| HTTP calls | {b['http_calls']} | {s['http_calls']} |\n"
        f"| Browser calls | {b['browser_calls']} | {s['browser_calls']} |\n"
        f"| Total measured cost | ${b['total_cost_usd']:.6f} | ${s['total_cost_usd']:.6f} |\n"
        f"| Median latency | {b['median_latency_ms']:.1f} ms | {s['median_latency_ms']:.1f} ms |\n"
        f"| P95 latency | {b['p95_latency_ms']:.1f} ms | {s['p95_latency_ms']:.1f} ms |\n"
        f"| Fallbacks | N/A | {s['fallbacks']} |\n"
        f"| LLM avoidance rate | N/A | {s['llm_avoidance_rate']:.1%} |\n\n"
        "## Smart Agent economics\n\n"
        f"- Capability acquisition cost: **${acquisition_cost:.6f}**\n"
        f"- Total relearning cost: **${relearning_cost:.6f}**\n"
        f"- Average baseline execution cost: **${baseline_avg:.6f}**\n"
        f"- Average deterministic Smart execution cost: **${deterministic_avg:.6f}**\n"
        f"- Measured cumulative savings: **${b['total_cost_usd'] - s['total_cost_usd']:.6f}**\n"
        f"- Simple break-even estimate: **{break_even_text}**\n\n"
        "The simple break-even estimate intentionally excludes long-run maintenance assumptions. Appendix A should use the raw ledger for the richer lifetime-cost model.\n"
    )
    report_path = out / "summary.md"
    report_path.write_text(md, encoding="utf-8")

    _cumulative_cost(rows, out / "cumulative_cost.png")
    _llm_calls(smart_rows, out / "llm_calls_by_execution.png")
    _latency(baseline_rows, smart_rows, out / "latency_by_architecture.png")
    return report_path


def _cumulative_cost(rows: list[ExecutionLedgerEntry], path: Path) -> None:
    groups: dict[str, list[ExecutionLedgerEntry]] = defaultdict(list)
    for row in rows:
        groups[row.architecture.value].append(row)
    plt.figure(figsize=(9, 5))
    for name, items in groups.items():
        total, cumulative = 0.0, []
        for item in items:
            total += item.total_cost_usd
            cumulative.append(total)
        plt.plot(range(1, len(items) + 1), cumulative, label=name)
    plt.xlabel("Execution number within architecture")
    plt.ylabel("Cumulative measured cost (USD)")
    plt.title("Chapter 3 — Cumulative Cost")
    plt.legend()
    plt.tight_layout(); plt.savefig(path, dpi=160); plt.close()


def _llm_calls(rows: list[ExecutionLedgerEntry], path: Path) -> None:
    plt.figure(figsize=(9, 5))
    plt.bar(range(1, len(rows) + 1), [r.model.calls for r in rows])
    plt.xlabel("Smart Agent execution number")
    plt.ylabel("LLM calls")
    plt.title("Chapter 3 — LLM Calls by Smart Execution")
    plt.tight_layout(); plt.savefig(path, dpi=160); plt.close()


def _latency(baseline: list[ExecutionLedgerEntry], smart: list[ExecutionLedgerEntry], path: Path) -> None:
    plt.figure(figsize=(8, 5))
    plt.boxplot([[r.latency_ms for r in baseline], [r.latency_ms for r in smart]], tick_labels=["Baseline", "Smart"])
    plt.ylabel("Latency (ms)")
    plt.title("Chapter 3 — Latency Distribution")
    plt.tight_layout(); plt.savefig(path, dpi=160); plt.close()
