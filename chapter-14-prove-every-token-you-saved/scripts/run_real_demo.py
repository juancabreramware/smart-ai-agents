from pathlib import Path
import sys
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.provider import OpenAIProvider
from src.runner import run
if __name__=="__main__":
    out=Path("evidence/demo-real-v2")
    reports=run(OpenAIProvider(),out,16,"demo")
    print("Real demo complete:",out)
    print(reports["evidence_grade_report.json"])
