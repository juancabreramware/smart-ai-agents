from pathlib import Path
import argparse,hashlib,zipfile
p=argparse.ArgumentParser();p.add_argument("--evidence-dir",required=True);a=p.parse_args()
d=Path(a.evidence_dir)
audit=d/"audit.json"
if not audit.exists() or '"passed": true' not in audit.read_text().lower():
    raise SystemExit("Audit must pass before freeze.")
out=d/"chapter-12-benchmark-real-v1-evidence.zip"
with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
    for f in sorted(d.iterdir()):
        if f.is_file() and f!=out: z.write(f,f.name)
b=out.read_bytes()
print(f"ZIP {out}\nSHA256 {hashlib.sha256(b).hexdigest().upper()}\nSIZE {len(b)}")
