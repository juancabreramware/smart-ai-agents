from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from smart_agents_ch7.portal.server import PortalHarness
from smart_agents_ch7.portal.state import PortalState


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", choices=["V1", "V2"], default="V1")
    args = ap.parse_args()
    state = PortalState(ui_version=args.version)
    with PortalHarness(state) as portal:
        print(f"HarborPoint portal {args.version}: {portal.base_url}")
        print("Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
