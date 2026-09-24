import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json,os,sys
from src.runner import run
if os.getenv("CH13_CONFIRM_CANONICAL")!="YES":
    raise SystemExit("Refusing canonical run. Set CH13_CONFIRM_CANONICAL=YES after all pre-run gates pass.")
provider=os.getenv("CH13_PROVIDER","openai")
print(json.dumps(run("evidence/benchmark-real-v1",provider,"canonical"),indent=2))
