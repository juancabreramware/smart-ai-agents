from pathlib import Path
import os,shutil,tempfile,py_compile

P=Path("src/provider.py"); R=Path("src/runner.py"); T=Path("src/typed_values.py")
def req(x,m):
    if not x: raise SystemExit("ABORTED WITHOUT SOURCE REPLACEMENT: "+m)

req(P.exists() and P.stat().st_size>0,"provider missing/empty")
req(R.exists() and R.stat().st_size>0,"runner missing/empty")
req(T.exists() and T.stat().st_size>0,"typed_values missing")
ps=P.read_text(encoding="utf-8"); rs=R.read_text(encoding="utf-8")

# Require exact recovered v1.0.3 characteristics.
req("from .numeric_normalization import numerically_equal" in ps,"expected v1.0.3 import missing")
req("same=numerically_equal(mv,cv)" in ps,"expected v1.0.3 comparison missing")
req("def _public_contract_with_semantics(" in ps,"_public_contract_with_semantics missing")
req('"public_contract":_public_contract_with_semantics(r)' in ps,"payload does not use semantics helper")
req("def normalize_decision(o,r):" in ps and "class MockProvider:" in ps,"provider structure incomplete")
req('"llm_call_count"' not in rs,"runner already has llm_call_count")
req('calls=sum(x["llm_called"] for x in rows)' in rs,"runner call-count anchor missing")

np=ps.replace("from .numeric_normalization import numerically_equal",
              "from .typed_values import value_type_for_operation,typed_equal",1)

# Patch the actual helper used by payload(). Locate helper structurally and insert
# value_type immediately before its return, regardless of local formatting.
hs=np.index("def _public_contract_with_semantics(")
he=np.index("\ndef ",hs+5)
hb=np[hs:he]
req("OPERATION_SEMANTICS" in hb,"semantics helper does not contain OPERATION_SEMANTICS")
req('"value_type"' not in hb,"value_type already present in semantics helper")

# The recovered v1.0.3 helper returns a dict variable or literal. We support both
# observed patterns without modifying contracts.py or hidden benchmark state.
if 'return {**c,"executable_semantics":OPERATION_SEMANTICS[op]}' in hb:
    hb2=hb.replace('return {**c,"executable_semantics":OPERATION_SEMANTICS[op]}',
                   'return {**c,"executable_semantics":OPERATION_SEMANTICS[op],"value_type":value_type_for_operation(op)}',1)
elif 'return {**base,"executable_semantics":OPERATION_SEMANTICS[op]}' in hb:
    hb2=hb.replace('return {**base,"executable_semantics":OPERATION_SEMANTICS[op]}',
                   'return {**base,"executable_semantics":OPERATION_SEMANTICS[op],"value_type":value_type_for_operation(op)}',1)
else:
    # Generic safe insertion for a helper with a dict assignment followed by return.
    lines=hb.splitlines()
    ret=[i for i,x in enumerate(lines) if x.lstrip().startswith("return ")]
    req(len(ret)==1,"unrecognized semantics-helper return shape")
    i=ret[0]
    expr=lines[i].strip()[7:]
    req(expr.isidentifier(),"unrecognized semantics-helper return expression")
    indent=lines[i][:len(lines[i])-len(lines[i].lstrip())]
    lines.insert(i,indent+f'{expr}["value_type"]=value_type_for_operation({expr}["operation"])')
    hb2="\n".join(lines)
req(hb2!=hb and '"value_type"' in hb2,"failed to install value_type")
np=np[:hs]+hb2+np[he:]

old='    mv=o["value"]; cv=canonical.value\n    try:\n        same=numerically_equal(mv,cv)\n    except ValueError as exc:\n        raise ValueError(f"Provider value is not a valid numeric value: model={mv!r}, canonical={cv!r}, raw={o!r}") from exc\n    if not same:\n        raise ValueError(f"Provider value conflicts with public contract: model={mv!r}, canonical={cv!r}, raw={o!r}")\n'
new='    mv=o["value"]; cv=canonical.value\n    kind=value_type_for_operation(c.operation)\n    try:\n        same=typed_equal(mv,cv,kind)\n    except ValueError as exc:\n        raise ValueError(f"Provider value violates typed public contract ({kind}): model={mv!r}, canonical={cv!r}, raw={o!r}") from exc\n    if not same:\n        raise ValueError(f"Provider value conflicts with public contract ({kind}): model={mv!r}, canonical={cv!r}, raw={o!r}")\n'
req(old in np,"v1.0.3 comparison block missing")
np=np.replace(old,new,1)

# Explicitly instruct model to honor the new public value_type.
prompt_old='"For a business decision, calculate action and value exactly from executable_semantics. "'
prompt_new='"For a business decision, calculate action and value exactly from executable_semantics. "\n            "Return value using public_contract.value_type exactly: boolean means JSON true or false (never 0, 1, or strings); "\n            "integer means a JSON integer; number means a JSON number. "'
req(prompt_old in np,"business-decision instruction anchor missing")
np=np.replace(prompt_old,prompt_new,1)

oldrow='"route":route,"llm_called":route in {"baseline_reasoning","initial_acquisition","reasoning_required","relearning"},"input_tokens":u.input_tokens'
newrow='"route":route,"llm_call_count":1 if route in {"baseline_reasoning","initial_acquisition","reasoning_required","relearning"} else 0,"llm_called":route in {"baseline_reasoning","initial_acquisition","reasoning_required","relearning"},"input_tokens":u.input_tokens'
req(oldrow in rs,"runner evidence-row anchor missing")
nr=rs.replace(oldrow,newrow,1)
nr=nr.replace('calls=sum(x["llm_called"] for x in rows)','calls=sum(x["llm_call_count"] for x in rows)',1)

# In-memory acceptance checks before touching working source.
req("numeric_normalization" not in np and "numerically_equal" not in np,"old numeric validator survived")
req("same=typed_equal(mv,cv,kind)" in np,"typed comparison absent")
req('"value_type"' in np[hs:np.index("\ndef ",hs+5)],"value_type absent from semantics helper")
req("Return value using public_contract.value_type exactly" in np,"typed prompt absent")
req('"llm_call_count":' in nr and 'calls=sum(x["llm_call_count"] for x in rows)' in nr,"runner hardening absent")

# Compile transformed candidates before source replacement.
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    for name,text in [("provider.py",np),("runner.py",nr),("typed_values.py",T.read_text(encoding="utf-8"))]:
        f=td/name; f.write_text(text,encoding="utf-8",newline="\n"); py_compile.compile(str(f),doraise=True)

B=Path("pre-v1042-backup"); B.mkdir(exist_ok=True)
shutil.copy2(P,B/"provider.py.v103"); shutil.copy2(R,B/"runner.py.v103")

def atomic(path,text):
    tmp=path.with_name(path.name+".v1042.tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

atomic(P,np); atomic(R,nr)
print("v1.0.4.2 applied atomically.")
print("Backups written to pre-v1042-backup.")
