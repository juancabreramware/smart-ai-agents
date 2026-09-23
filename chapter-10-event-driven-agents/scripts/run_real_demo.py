import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path
import json
from src.runner import run
m=run(Path("evidence/real-demo"),demo=True)
print(json.dumps(m,indent=2))
