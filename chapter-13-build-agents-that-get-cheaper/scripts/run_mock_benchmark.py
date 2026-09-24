import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
from src.runner import run
print(json.dumps(run("evidence/benchmark-mock-v1","mock","canonical"),indent=2))
