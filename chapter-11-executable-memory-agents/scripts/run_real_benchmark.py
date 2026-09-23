import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path
import json,os
if os.getenv("CH11_PROVIDER","").lower()!="openai":raise SystemExit("Set CH11_PROVIDER=openai")
for k in ("CH11_INPUT_USD_PER_MILLION","CH11_OUTPUT_USD_PER_MILLION"):
    if not os.getenv(k) or float(os.getenv(k,"0"))<=0:raise SystemExit(f"Set positive pinned {k}")
from src.provider import from_env
from src.runner import run
print(json.dumps(run("canonical",from_env(),Path("evidence/benchmark-real-v1")),indent=2))
