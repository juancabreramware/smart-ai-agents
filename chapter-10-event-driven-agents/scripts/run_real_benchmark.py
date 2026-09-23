import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path
import os, json
if os.getenv("CH10_PROVIDER","mock").lower()=="mock":
    raise SystemExit("Refusing canonical real benchmark with mock provider. Set CH10_PROVIDER=openai.")
if not os.getenv("CH10_INPUT_USD_PER_MILLION") or not os.getenv("CH10_OUTPUT_USD_PER_MILLION"):
    raise SystemExit("Freeze pricing first: set CH10_INPUT_USD_PER_MILLION and CH10_OUTPUT_USD_PER_MILLION.")
from src.runner import run
m=run(Path("evidence/benchmark-real-v1"),demo=False)
print(json.dumps(m,indent=2))
