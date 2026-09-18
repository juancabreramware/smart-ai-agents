import argparse,hashlib,zipfile
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('evidence'); p.add_argument('--name',required=True); a=p.parse_args(); d=Path(a.evidence); z=d/a.name
files=[x for x in d.iterdir() if x.is_file() and x!=z]
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as q:
    for f in sorted(files): q.write(f,f.name)
h=hashlib.sha256(z.read_bytes()).hexdigest(); print('Evidence ZIP:',z); print('SHA-256:',h)
