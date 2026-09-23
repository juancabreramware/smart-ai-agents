import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path
import os, json
os.environ["CH10_PROVIDER"]="mock"
from src.runner import run
m=run(Path("evidence/mock"),demo=False)
print(json.dumps(m,indent=2))
