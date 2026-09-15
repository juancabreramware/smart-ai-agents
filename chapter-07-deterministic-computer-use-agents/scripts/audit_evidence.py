from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from smart_agents_ch7.benchmark.audit import audit_directory


def main() -> int:
    ap = argparse.ArgumentParser(description="Independently recompute Chapter 7 benchmark metrics from raw JSONL ledgers.")
    ap.add_argument("evidence_dir", type=Path)
    args = ap.parse_args()
    report = audit_directory(args.evidence_dir)
    path = args.evidence_dir / "audit-report.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passes_basic_integrity"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
