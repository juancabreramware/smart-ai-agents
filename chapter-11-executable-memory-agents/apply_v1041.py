from pathlib import Path
import os,shutil,tempfile,py_compile
P=Path("src/provider.py"); R=Path("src/runner.py"); T=Path("src/typed_values.py")
def req(x,m):
    if not x: raise SystemExit("ABORTED WITHOUT SOURCE REPLACEMENT: "+m)
req(P.exists() and P.stat().st_size>0,"provider missing/empty")
req(R.exists() and R.stat().st_size>0,"runner missing/empty")
ps=P.read_text(encoding="utf-8"); rs=R.read_text(encoding="utf-8")
req("from .numeric_normalization import numerically_equal" in ps,"expected v1.0.3 import missing")
req("same=numerically_equal(mv,cv)" in ps,"expected v1.0.3 comparison missing")
req("def payload(r,task):" in ps and "def normalize_decision(o,r):" in ps and "class MockProvider:" in ps,"provider structure incomplete")
req('calls=sum(x["llm_called"] for x in rows)' in rs,"runner baseline anchor missing")
np=ps.replace("from .numeric_normalization import numerically_equal","from .typed_values import value_type_for_operation,typed_equal",1)
start=np.index("def payload(r,task):"); end=np.index("def normalize_decision(o,r):"); block=np[start:end]
a='"public_contract":public_contract(r.family,r.contract_version)'
b='"public_contract":{**public_contract(r.family,r.contract_version),"value_type":value_type_for_operation(get_contract(r.family,r.contract_version).operation)}'
if a not in block:
    a='"public_contract": public_contract(r.family,r.contract_version)'
    b='"public_contract": {**public_contract(r.family,r.contract_version),"value_type":value_type_for_operation(get_contract(r.family,r.contract_version).operation)}'
req(a in block,"public_contract payload anchor missing")
block=block.replace(a,b,1); np=np[:start]+block+np[end:]
old='    mv=o["value"]; cv=canonical.value\n    try:\n        same=numerically_equal(mv,cv)\n    except ValueError as exc:\n        raise ValueError(f"Provider value is not a valid numeric value: model={mv!r}, canonical={cv!r}, raw={o!r}") from exc\n    if not same:\n        raise ValueError(f"Provider value conflicts with public contract: model={mv!r}, canonical={cv!r}, raw={o!r}")\n'
new='    mv=o["value"]; cv=canonical.value\n    kind=value_type_for_operation(c.operation)\n    try:\n        same=typed_equal(mv,cv,kind)\n    except ValueError as exc:\n        raise ValueError(f"Provider value violates typed public contract ({kind}): model={mv!r}, canonical={cv!r}, raw={o!r}") from exc\n    if not same:\n        raise ValueError(f"Provider value conflicts with public contract ({kind}): model={mv!r}, canonical={cv!r}, raw={o!r}")\n'
req(old in np,"comparison block missing"); np=np.replace(old,new,1)
oldrow='"route":route,"llm_called":route in {"baseline_reasoning","initial_acquisition","reasoning_required","relearning"},"input_tokens":u.input_tokens'
newrow='"route":route,"llm_call_count":1 if route in {"baseline_reasoning","initial_acquisition","reasoning_required","relearning"} else 0,"llm_called":route in {"baseline_reasoning","initial_acquisition","reasoning_required","relearning"},"input_tokens":u.input_tokens'
req(oldrow in rs,"runner row anchor missing"); nr=rs.replace(oldrow,newrow,1).replace('calls=sum(x["llm_called"] for x in rows)','calls=sum(x["llm_call_count"] for x in rows)',1)
req("numerically_equal" not in np and "typed_equal(mv,cv,kind)" in np,"provider transformation validation failed")
req('"value_type":value_type_for_operation' in np,"value_type transformation validation failed")
req('"llm_call_count":' in nr and 'calls=sum(x["llm_call_count"] for x in rows)' in nr,"runner transformation validation failed")
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    for name,text in [("provider.py",np),("runner.py",nr),("typed_values.py",T.read_text(encoding="utf-8"))]:
        f=td/name; f.write_text(text,encoding="utf-8",newline="\n"); py_compile.compile(str(f),doraise=True)
B=Path("pre-v1041-backup"); B.mkdir(exist_ok=True); shutil.copy2(P,B/"provider.py.v103"); shutil.copy2(R,B/"runner.py.v103")
def atomic(path,text):
    t=path.with_name(path.name+".v1041.tmp"); t.write_text(text,encoding="utf-8",newline="\n"); os.replace(t,path)
atomic(P,np); atomic(R,nr)
print("v1.0.4.1 applied atomically.")
