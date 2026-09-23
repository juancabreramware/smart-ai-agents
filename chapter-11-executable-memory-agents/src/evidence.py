import json
def write_json(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,sort_keys=True,default=str),encoding="utf-8")
def write_jsonl(p,a):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text("".join(json.dumps(x,sort_keys=True,default=str,separators=(",",":"))+"\n" for x in a),encoding="utf-8")
def read_jsonl(p):return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
