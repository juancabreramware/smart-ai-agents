import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse, hashlib, json, zipfile
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument("--evidence-dir",required=True)
a=p.parse_args()
d=Path(a.evidence_dir)
audit=json.loads((d/"audit.json").read_text(encoding="utf-8"))
if not audit.get("passed"):
    raise SystemExit("Audit has not passed. Evidence will not be frozen.")
zip_path=d/f"chapter-10-{d.name}-evidence.zip"
with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as z:
    for f in sorted(d.iterdir()):
        if f.is_file() and f!=zip_path:
            z.write(f,f.name)
h=hashlib.sha256(zip_path.read_bytes()).hexdigest().upper()
print(f"ZIP: {zip_path}")
print(f"SHA256: {h}")
print(f"SIZE: {zip_path.stat().st_size}")
