from pathlib import Path
import os,shutil,tempfile,py_compile
P=Path("src/provider.py")
def req(x,m):
    if not x: raise SystemExit("ABORTED WITHOUT SOURCE REPLACEMENT: "+m)
req(P.exists() and P.stat().st_size>0,"provider missing/empty")
ps=P.read_text(encoding="utf-8")
req("def _strict_response_schema(p):" in ps,"v1.0.5.0 strict schema missing")
req("def _parse_strict_response(r):" in ps,"v1.0.5.0 strict parser missing")
req("from .typed_values import value_type_for_operation,typed_equal" in ps,"v1.0.4.2 typed contract missing")
req("OPERATION_SEMANTICS={" in ps,"OPERATION_SEMANTICS missing")
start=ps.index("OPERATION_SEMANTICS={")
end=ps.index("\ndef _public_contract_with_semantics(r):",start)
new_block='OPERATION_SEMANTICS={\n    "inventory_reorder":{"steps":["triggered = (on_hand - reserved) < (reorder_point + safety_buffer)","if triggered: action = reorder","otherwise: action = no_action"],"value_rule":{"reorder":"order_quantity","no_action":"0"}},\n    "shipment_sla":{"steps":["triggered = eta_hours > (promised_hours + grace_hours)","if triggered: action = escalate","otherwise: action = no_action"],"value_rule":{"escalate":"true","no_action":"false"}},\n    "invoice_escalation":{"steps":["triggered = days_overdue > days_threshold AND amount >= amount_threshold","if triggered: action = escalate","otherwise: action = no_action"],"value_rule":{"escalate":"true","no_action":"false"}},\n    "supplier_score":{"steps":["score = round(on_time_pct * on_time_weight + quality_pct * quality_weight, 2)","if score < action_threshold: action = review","otherwise: action = no_action"],"value_rule":{"review":"score","no_action":"score"}},\n    "customer_action":{"steps":["triggered = risk_score > risk_threshold AND past_due is true","if triggered: action = review","otherwise: action = no_action"],"value_rule":{"review":"true","no_action":"false"}},\n    "order_priority":{"steps":["triggered = age_hours > sla_hours OR priority_flag is true","if triggered: action = prioritize","otherwise: action = no_action"],"value_rule":{"prioritize":"true","no_action":"false"}}\n}'
np=ps[:start]+new_block+ps[end:]
for bad in ("target_stock","priority_window_hours","on_time_rate","quality_rate","minimum_score","balance_threshold","hold_account","review_supplier",'"place_order"'):
    req(bad not in np,"withdrawn public-semantics token still present: "+bad)
for good in ('"reorder":"order_quantity"','"escalate":"true"',"days_overdue > days_threshold AND amount >= amount_threshold","round(on_time_pct * on_time_weight + quality_pct * quality_weight, 2)","risk_score > risk_threshold AND past_due is true","age_hours > sla_hours OR priority_flag is true"):
    req(good in np,"required aligned semantic missing: "+good)
with tempfile.TemporaryDirectory() as td:
    f=Path(td)/"provider.py"; f.write_text(np,encoding="utf-8",newline="\n"); py_compile.compile(str(f),doraise=True)
B=Path("pre-v1051-backup"); B.mkdir(exist_ok=True); shutil.copy2(P,B/"provider.py.v1050")
tmp=P.with_name(P.name+".v1051.tmp"); tmp.write_text(np,encoding="utf-8",newline="\n"); os.replace(tmp,P)
print("v1.0.5.1 applied atomically.")
print("Backup written to pre-v1051-backup/provider.py.v1050")
