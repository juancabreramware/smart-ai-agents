from pathlib import Path
p=Path("src/provider.py");s=p.read_text(encoding="utf-8")
s=s.replace("from .numeric_normalization import numerically_equal\\n","from .typed_values import value_type_for_operation,typed_equal\\n")
a='return {**c,"executable_semantics":OPERATION_SEMANTICS[op]}'
z='return {**c,"executable_semantics":OPERATION_SEMANTICS[op],"value_type":value_type_for_operation(op)}'
if a in s:s=s.replace(a,z,1)
elif '"value_type":value_type_for_operation(op)' not in s:raise SystemExit("public contract anchor missing")
old='    mv=o["value"]; cv=canonical.value\n    try:\n        same=numerically_equal(mv,cv)\n    except ValueError as exc:\n        raise ValueError(f"Provider value is not a valid numeric value: model={mv!r}, canonical={cv!r}, raw={o!r}") from exc\n    if not same:\n        raise ValueError(f"Provider value conflicts with public contract: model={mv!r}, canonical={cv!r}, raw={o!r}")\n'
new='    mv=o["value"]; cv=canonical.value\n    kind=value_type_for_operation(c.operation)\n    try:\n        same=typed_equal(mv,cv,kind)\n    except ValueError as exc:\n        raise ValueError(f"Provider value violates typed public contract ({kind}): model={mv!r}, canonical={cv!r}, raw={o!r}") from exc\n    if not same:\n        raise ValueError(f"Provider value conflicts with public contract ({kind}): model={mv!r}, canonical={cv!r}, raw={o!r}")\n'
if old in s:s=s.replace(old,new,1)
elif "same=typed_equal(mv,cv,kind)" not in s:raise SystemExit("v1.0.3 comparison anchor missing")
a='"For a business decision, calculate action and value exactly from executable_semantics. "'
z=a+'\\n            "Return value using exactly public_contract.value_type: boolean means JSON true/false (never 0/1 or strings); integer means a JSON integer; number means a JSON number. "'
if a in s:s=s.replace(a,z,1)
elif "Return value using exactly public_contract.value_type" not in s:raise SystemExit("prompt anchor missing")
p.write_text(s,encoding="utf-8",newline="\n")
r=Path("src/runner.py");q=r.read_text(encoding="utf-8")
a='"route":route,"llm_called":route in {"baseline_reasoning","initial_acquisition","reasoning_required","relearning"},"input_tokens":u.input_tokens'
z='"route":route,"llm_call_count":1 if route in {"baseline_reasoning","initial_acquisition","reasoning_required","relearning"} else 0,"llm_called":route in {"baseline_reasoning","initial_acquisition","reasoning_required","relearning"},"input_tokens":u.input_tokens'
if a in q:q=q.replace(a,z,1)
elif '"llm_call_count":' not in q:raise SystemExit("runner row anchor missing")
q=q.replace('calls=sum(x["llm_called"] for x in rows)','calls=sum(x["llm_call_count"] for x in rows)')
r.write_text(q,encoding="utf-8",newline="\n")
print("v1.0.4 applied.")

