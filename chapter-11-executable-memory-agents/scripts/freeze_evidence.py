import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse,hashlib,zipfile
from pathlib import Path
from src.audit import audit
p=argparse.ArgumentParser();p.add_argument("--evidence-dir",required=True);a=p.parse_args();d=Path(a.evidence_dir);r=audit(d)
if not r["passed"]:raise SystemExit(f"Audit failed: {r['errors']}")
z=d/"chapter-11-benchmark-real-v1-evidence.zip"
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED) as f:
    for x in sorted(d.iterdir()):
        if x.is_file() and x!=z:f.write(x,x.name)
print(f"ZIP: {z}\nSHA256: {hashlib.sha256(z.read_bytes()).hexdigest().upper()}\nSIZE: {z.stat().st_size}")
