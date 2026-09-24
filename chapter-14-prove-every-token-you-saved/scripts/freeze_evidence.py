from pathlib import Path
import sys
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import argparse,json,hashlib,zipfile
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--evidence-dir",required=True)
    args=ap.parse_args(); d=Path(args.evidence_dir)
    audit=json.loads((d/"audit_report.json").read_text(encoding="utf-8"))
    if not audit.get("passed"):
        raise SystemExit("Refusing freeze: audit did not pass.")
    z=d/"chapter-14-benchmark-real-v1-evidence.zip"
    names=[p for p in d.iterdir() if p.is_file() and p!=z]
    with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED) as f:
        for p in sorted(names): f.write(p,p.name)
    print("ZIP",z)
    print("SHA256",hashlib.sha256(z.read_bytes()).hexdigest().upper())
    print("SIZE",z.stat().st_size)
