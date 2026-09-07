"""Run one Reasoning-First baseline execution."""
from __future__ import annotations

# Allow this file to be executed directly as `python experiments/<script>.py`
# without requiring the project to be installed as a package first.
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
import argparse
from experiments.helpers import controlled_task, ground_truth
from smart_agent.baseline_agent import BaselineAgent
from smart_agent.model_provider import provider_from_name
from smart_agent.telemetry import LedgerWriter

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "benchmark_site" / "current_version.txt"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--provider", default="openai", choices=["openai", "mock"])
    p.add_argument("--experiment-id", default="chapter3-manual")
    args = p.parse_args()
    version = VERSION_FILE.read_text().strip()
    result, ledger = BaselineAgent(provider_from_name(args.provider)).run(
        task=controlled_task(), experiment_id=args.experiment_id,
        phase=f"MANUAL_{version.upper()}", ground_truth_path=ground_truth(version)
    )
    LedgerWriter(args.experiment_id).append(ledger)
    print(result.model_dump_json(indent=2))
    print(f"\npath={ledger.path.value} model_calls={ledger.model.calls} validation={ledger.validation_passed} cost=${ledger.total_cost_usd:.6f}")
    for note in ledger.notes:
        print(f"  - {note}")


if __name__ == "__main__":
    main()
