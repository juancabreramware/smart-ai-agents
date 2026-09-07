"""Optional realism test against reader-configured public vendor pricing pages."""
from __future__ import annotations

# Allow this file to be executed directly as `python experiments/<script>.py`
# without requiring the project to be installed as a package first.
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
import argparse
import yaml
from smart_agent.baseline_agent import BaselineAgent
from smart_agent.model_provider import provider_from_name
from smart_agent.models import TaskDescriptor
from smart_agent.smart_agent import SmartPricingAgent

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--provider", default="openai", choices=["openai", "mock"])
    p.add_argument("--config", required=True)
    p.add_argument("--architecture", default="smart", choices=["smart", "baseline"])
    args = p.parse_args()
    cfg = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))
    provider = provider_from_name(args.provider)
    agent = SmartPricingAgent(provider) if args.architecture == "smart" else BaselineAgent(provider)

    for vendor in cfg.get("vendors", []):
        task = TaskDescriptor(
            vendor_id=vendor["id"], vendor_name=vendor["name"], domain=vendor["domain"],
            pricing_url=vendor.get("pricing_url"), search_query=vendor.get("search_query")
        )
        result, ledger = agent.run(task=task, experiment_id="chapter3-live", phase="LIVE", ground_truth_path=None)
        print("\n" + "=" * 70)
        print(vendor["name"])
        print(result.model_dump_json(indent=2))
        print(f"path={ledger.path.value} model_calls={ledger.model.calls} validation={ledger.validation_passed}")
        for note in ledger.notes:
            print(f"  - {note}")


if __name__ == "__main__":
    main()
