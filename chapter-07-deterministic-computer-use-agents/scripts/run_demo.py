from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from smart_agents_ch7.benchmark.runner import run_suite
from smart_agents_ch7.benchmark.workload import load_jsonl


def main() -> int:
    ap = argparse.ArgumentParser(description="Run the Chapter 7 15-request demonstration workload.")
    ap.add_argument("--planner", choices=["mock", "openai"], default="mock")
    ap.add_argument("--workload", type=Path, default=ROOT / "workloads" / "demo_v1.0.jsonl")
    ap.add_argument("--output", type=Path, default=ROOT / "evidence" / "demo-mock")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--executor", choices=["playwright", "simulated"], default="playwright")
    args = ap.parse_args()
    requests = load_jsonl(args.workload)
    if len(requests) != 15:
        raise SystemExit(f"Demo workload must contain exactly 15 requests; got {len(requests)}")
    summary = run_suite(requests, args.planner, args.output, workload_path=args.workload, headless=not args.headed, executor_name=args.executor)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
