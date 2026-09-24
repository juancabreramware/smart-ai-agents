import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json,os
from src.runner import run
provider=os.getenv("CH13_PROVIDER","openai")
print(json.dumps(run("evidence/demo-real-v1",provider,"demo",request_limit=16),indent=2))
