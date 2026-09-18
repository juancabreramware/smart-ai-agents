from __future__ import annotations
import json
from pathlib import Path
def load(path):
    return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
