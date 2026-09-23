from pathlib import Path
import sys, json, os
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.runner import run
if os.getenv("CH12_CONFIRM_CANONICAL")!="YES":
    raise SystemExit("Refusing paid canonical run. Set CH12_CONFIRM_CANONICAL=YES after all gates pass.")
provider=os.getenv("CH12_PROVIDER","openai")
m,s,o=run(provider,"canonical","evidence/benchmark-real-v1")
print(json.dumps({"manifest":m,"summary":s,"output_dir":str(o)},indent=2))
