from pathlib import Path
import os,shutil,tempfile,py_compile
P=Path("src/provider.py")
def req(x,m):
    if not x: raise SystemExit("ABORTED WITHOUT SOURCE REPLACEMENT: "+m)
req(P.exists() and P.stat().st_size>0,"provider missing/empty")
ps=P.read_text(encoding="utf-8")
req("from .typed_values import value_type_for_operation,typed_equal" in ps,"v1.0.4.2 typed import missing")
req('return {**c,"executable_semantics":OPERATION_SEMANTICS[op],"value_type":value_type_for_operation(op)}' in ps,"v1.0.4.2 public typed contract missing")
req("class OpenAIProvider:" in ps,"OpenAIProvider missing")
req('r=self.client.responses.create(model=self.model,input=json.dumps(p,sort_keys=True))' in ps,"expected OpenAI Responses call missing")
req('return parse(r.output_text),_usage(r,ms,self.ip,self.op)' in ps,"expected free-form parse boundary missing")
helper = """
def _strict_response_schema(p):
    task=p.get("task")
    if task=="acquire_or_relearn_capability":
        schema={"type":"object","properties":{
            "family":{"type":"string"},"contract_version":{"type":"string"},"operation":{"type":"string"},
            "dependencies":{"type":"array","items":{"type":"string"}},"policy_fingerprint":{"type":"string"},
            "environment_fingerprint":{"type":"string"}},
            "required":["family","contract_version","operation","dependencies","policy_fingerprint","environment_fingerprint"],
            "additionalProperties":False}
        return {"type":"json_schema","name":"chapter11_capability_acquisition","strict":True,"schema":schema}
    if task=="produce_current_business_decision":
        kind=p["public_contract"]["value_type"]
        value_schema={"boolean":{"type":"boolean"},"integer":{"type":"integer"},"number":{"type":"number"}}.get(kind)
        if value_schema is None: raise ValueError(f"Unsupported public_contract.value_type={kind!r}")
        schema={"type":"object","properties":{
            "action":{"type":"string"},"value":value_schema,
            "label":{"type":["string","null"],"enum":["weather","customs","damage","policy_exception","unknown",None]}},
            "required":["action","value","label"],"additionalProperties":False}
        return {"type":"json_schema","name":f"chapter11_business_decision_{kind}","strict":True,"schema":schema}
    raise ValueError(f"No strict response schema for task={task!r}")

def _parse_strict_response(r):
    status=getattr(r,"status",None)
    if status!="completed":
        details=getattr(r,"incomplete_details",None)
        raise ValueError(f"OpenAI response did not complete: status={status!r}, incomplete_details={details!r}")
    text=getattr(r,"output_text",None)
    if not text: raise ValueError("OpenAI strict structured response contained no output_text")
    try: o=json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"OpenAI strict structured response was not valid JSON: {text[:500]!r}") from exc
    if not isinstance(o,dict): raise ValueError("OpenAI strict structured response must be a JSON object")
    return o
"""
i=ps.index("class OpenAIProvider:")
np=ps[:i]+helper+"\n"+ps[i:]
old="    def call(self,p):\n        t=time.perf_counter()\n        r=self.client.responses.create(model=self.model,input=json.dumps(p,sort_keys=True))\n        ms=(time.perf_counter()-t)*1000\n        return parse(r.output_text),_usage(r,ms,self.ip,self.op)\n"
new="    def call(self,p):\n        t=time.perf_counter()\n        fmt=_strict_response_schema(p)\n        r=self.client.responses.create(\n            model=self.model,\n            input=json.dumps(p,sort_keys=True),\n            text={\"format\":fmt}\n        )\n        ms=(time.perf_counter()-t)*1000\n        return _parse_strict_response(r),_usage(r,ms,self.ip,self.op)\n"
req(old in np,"OpenAIProvider.call exact block missing")
np=np.replace(old,new,1)
req('text={"format":fmt}' in np,"strict text.format not installed")
req('"strict":True' in np and '"additionalProperties":False' in np,"strict closed schema missing")
req("return parse(r.output_text)" not in np,"free-form recovery still used by OpenAIProvider")
with tempfile.TemporaryDirectory() as td:
    f=Path(td)/"provider.py"; f.write_text(np,encoding="utf-8",newline="\n"); py_compile.compile(str(f),doraise=True)
B=Path("pre-v1050-backup"); B.mkdir(exist_ok=True); shutil.copy2(P,B/"provider.py.v1042")
tmp=P.with_name(P.name+".v1050.tmp"); tmp.write_text(np,encoding="utf-8",newline="\n"); os.replace(tmp,P)
print("v1.0.5.0 applied atomically.")
print("Backup written to pre-v1050-backup/provider.py.v1042")
