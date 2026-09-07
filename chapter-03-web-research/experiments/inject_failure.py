"""Switch the controlled site between structural versions."""
from __future__ import annotations

# Allow this file to be executed directly as `python experiments/<script>.py`
# without requiring the project to be installed as a package first.
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
import argparse

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "benchmark_site" / "current_version.txt"


def set_version(version: str) -> None:
    target = ROOT / "benchmark_site" / version / "pricing.html"
    if not target.exists():
        raise ValueError(f"Unknown site version {version!r}")
    VERSION_FILE.write_text(version + "\n", encoding="utf-8")
    print(f"[site] switched controlled benchmark site to {version}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--version", required=True, choices=["v1", "v2", "v3"])
    args = p.parse_args()
    set_version(args.version)


if __name__ == "__main__":
    main()
