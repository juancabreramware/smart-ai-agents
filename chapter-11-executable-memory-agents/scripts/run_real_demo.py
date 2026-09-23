import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path
import json,os
os.environ["CH11_PROVIDER"]="openai"
from src.provider import from_env
from src.runner import run
print(json.dumps(run("demo",from_env(),Path("evidence/real-demo")),indent=2))
