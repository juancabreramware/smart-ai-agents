from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import zipfile


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="Freeze an audited Chapter 7 evidence directory into a hash-stamped ZIP.")
    ap.add_argument("evidence_dir", type=Path)
    ap.add_argument("--name", default="chapter-07-evidence-v1.0.zip")
    args = ap.parse_args()
    root = args.evidence_dir.resolve()
    required = [
        "experiment-manifest.json", "execution-summary.json", "audit-report.json",
        "baseline-executions.jsonl", "smart-executions.jsonl", "naive-executions.jsonl",
        "smart-capability-registry.json",
    ]
    missing = [name for name in required if not (root / name).exists()]
    if missing:
        raise SystemExit("Cannot freeze; missing: " + ", ".join(missing))
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.name not in {"SHA256SUMS.txt", args.name})
    sums = "\n".join(f"{sha(p)}  {p.relative_to(root).as_posix()}" for p in files) + "\n"
    (root / "SHA256SUMS.txt").write_text(sums, encoding="utf-8")
    zip_path = root / args.name
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted([*files, root / "SHA256SUMS.txt"]):
            z.write(p, p.relative_to(root).as_posix())
    print(f"Evidence ZIP: {zip_path}")
    print(f"SHA-256: {sha(zip_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
