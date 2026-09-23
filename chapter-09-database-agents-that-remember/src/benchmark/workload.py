import json
def load(path): return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
