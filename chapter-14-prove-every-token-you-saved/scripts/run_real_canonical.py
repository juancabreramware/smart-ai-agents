from pathlib import Path
import sys
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import os
from src.provider import OpenAIProvider
from src.runner import run
if __name__=="__main__":
    if os.environ.get("CH14_CONFIRM_CANONICAL")!="YES":
        raise SystemExit("Refusing canonical run. Set CH14_CONFIRM_CANONICAL=YES after all gates pass.")
    out=Path("evidence/benchmark-real-v1")
    if out.exists() and any(out.iterdir()):
        raise SystemExit("Refusing to overwrite existing canonical evidence directory.")
    reports=run(OpenAIProvider(),out,240,"canonical")
    print("Canonical benchmark complete:",out)
    print(reports["evidence_grade_report.json"])
