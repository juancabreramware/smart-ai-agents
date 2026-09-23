import argparse,hashlib,zipfile
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('evidence'); p.add_argument('--name',required=True); a=p.parse_args(); d=Path(a.evidence); name=a.name if a.name.endswith('.zip') else a.name+'.zip'; z=d/name
files=[x for x in d.rglob('*') if x.is_file() and x!=z]
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as q:
    for f in sorted(files): q.write(f,f.relative_to(d))
h=hashlib.sha256(z.read_bytes()).hexdigest(); print(f'Evidence ZIP: {z}'); print(f'SHA-256: {h}')
