import argparse,hashlib,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument("--evidence-dir",required=True);a=p.parse_args()
d=Path(a.evidence_dir)
audit=d/"audit.json"
if not audit.exists() or '"passed": true' not in audit.read_text(encoding="utf-8").lower():
    raise SystemExit("Refusing freeze: audit.json missing or not passed.")
z=d/"chapter-13-benchmark-real-v1-evidence.zip"
with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED) as out:
    for f in sorted(d.iterdir()):
        if f.is_file() and f!=z: out.write(f,f.name)
h=hashlib.sha256(z.read_bytes()).hexdigest().upper()
print("ZIP",z);print("SHA256",h);print("SIZE",z.stat().st_size)
