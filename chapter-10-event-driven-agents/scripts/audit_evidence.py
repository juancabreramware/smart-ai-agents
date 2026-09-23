import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse, json
from pathlib import Path
from src.audit import audit
p=argparse.ArgumentParser()
p.add_argument("--evidence-dir",required=True)
a=p.parse_args()
r=audit(Path(a.evidence_dir))
print(json.dumps(r,indent=2))
raise SystemExit(0 if r["passed"] else 1)
