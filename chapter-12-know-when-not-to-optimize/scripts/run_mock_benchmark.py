from pathlib import Path
import sys, json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.runner import run
m,s,o=run("mock","canonical","evidence/mock-v1")
print(json.dumps({"manifest":m,"summary":s,"output_dir":str(o)},indent=2))
