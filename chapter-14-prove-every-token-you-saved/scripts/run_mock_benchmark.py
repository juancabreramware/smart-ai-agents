from pathlib import Path
import sys
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.mock_provider import MockProvider
from src.runner import run
if __name__=="__main__":
    out=Path("evidence/benchmark-mock-v1")
    reports=run(MockProvider(),out,240,"mock")
    print("Mock benchmark complete:",out)
    print(reports["evidence_grade_report.json"])
