from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def audit_directory(evidence_dir: Path) -> dict[str, Any]:
    raw = {name: _read_jsonl(evidence_dir / f"{name}-executions.jsonl") for name in ("baseline", "smart", "naive")}
    ids = {name: [r["request"]["request_id"] for r in rows] for name, rows in raw.items()}
    identical_order = ids["baseline"] == ids["smart"] == ids["naive"]

    report: dict[str, Any] = {
        "schema_version": 1,
        "identical_request_ids_and_order": identical_order,
        "architectures": {},
    }
    for name, rows in raw.items():
        n = len(rows)
        correct = sum(bool(r["audit"]["ok"]) for r in rows)
        llm_calls = sum(bool(r["llm_called"]) for r in rows)
        stale = sum(bool(r["stale_reuse"]) for r in rows)
        cost = sum(float(r["measured_llm_cost"]) for r in rows)
        routes: dict[str, int] = {}
        for r in rows:
            routes[r["routing_path"]] = routes.get(r["routing_path"], 0) + 1
        report["architectures"][name] = {
            "requests": n,
            "correct": correct,
            "incorrect": n - correct,
            "correctness_pct": round(correct / n * 100, 4) if n else 0.0,
            "llm_calls": llm_calls,
            "llm_avoidance_pct": round((n - llm_calls) / n * 100, 4) if n else 0.0,
            "stale_incorrect_reuses": stale,
            "measured_llm_cost_usd": round(cost, 10),
            "routing": routes,
        }
    report["passes_basic_integrity"] = identical_order and all(v["requests"] == len(raw["baseline"]) for v in report["architectures"].values())
    return report
