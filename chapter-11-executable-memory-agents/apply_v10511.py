from pathlib import Path
import os,shutil,tempfile,py_compile
PROVIDER=Path("src/provider.py")
TEST=Path("tests/test_public_semantics_alignment_v1051.py")
def req(ok,msg):
    if not ok: raise SystemExit("ABORTED WITHOUT SOURCE REPLACEMENT: "+msg)
req(PROVIDER.exists() and PROVIDER.stat().st_size>0,"src/provider.py missing/empty")
req(TEST.exists() and TEST.stat().st_size>0,"v1.0.5.1 alignment test missing")
ps=PROVIDER.read_text(encoding="utf-8")
ts=TEST.read_text(encoding="utf-8")
old='"inventory_reorder":{"steps":["triggered = (on_hand - reserved) < (reorder_point + safety_buffer)","if triggered: action = reorder","otherwise: action = no_action"],"value_rule":{"reorder":"order_quantity","no_action":"0"}}'
new='"inventory_reorder":{"steps":["available = on_hand - reserved","trigger_level = reorder_point + safety_buffer","triggered = available < trigger_level","if triggered: action = reorder","otherwise: action = no_action"],"value_rule":{"reorder":"order_quantity","no_action":"0"}}'
req(ps.count(old)==1,"expected v1.0.5.1 inventory semantics anchor not found exactly once")
req(ts.count(old)==1,"expected v1.0.5.1 test expectation anchor not found exactly once")
nps=ps.replace(old,new,1)
nts=ts.replace(old,new,1)
for required in ("def _strict_response_schema(p):","def _parse_strict_response(r):","from .typed_values import value_type_for_operation,typed_equal","days_overdue > days_threshold AND amount >= amount_threshold","round(on_time_pct * on_time_weight + quality_pct * quality_weight, 2)","risk_score > risk_threshold AND past_due is true","age_hours > sla_hours OR priority_flag is true"): req(required in nps,"required prior hardening missing: "+required)
for bad in ("target_stock","priority_window_hours","on_time_rate","quality_rate","minimum_score","balance_threshold","hold_account","review_supplier",'"place_order"'): req(bad not in nps,"withdrawn public-semantics token present: "+bad)
for required in ("available = on_hand - reserved","trigger_level = reorder_point + safety_buffer","triggered = available < trigger_level",'"reorder":"order_quantity"'): req(required in nps,"corrected inventory semantic missing: "+required)
with tempfile.TemporaryDirectory() as td:
    ptmp=Path(td)/"provider.py"; ttmp=Path(td)/"test_public_semantics_alignment_v1051.py"
    ptmp.write_text(nps,encoding="utf-8",newline="\n"); ttmp.write_text(nts,encoding="utf-8",newline="\n")
    py_compile.compile(str(ptmp),doraise=True); py_compile.compile(str(ttmp),doraise=True)
backup=Path("pre-v10511-backup"); backup.mkdir(exist_ok=True)
shutil.copy2(PROVIDER,backup/"provider.py.v1051"); shutil.copy2(TEST,backup/"test_public_semantics_alignment_v1051.py.v1051")
pt=PROVIDER.with_name(PROVIDER.name+".v10511.tmp"); tt=TEST.with_name(TEST.name+".v10511.tmp")
pt.write_text(nps,encoding="utf-8",newline="\n"); tt.write_text(nts,encoding="utf-8",newline="\n")
os.replace(pt,PROVIDER)
try: os.replace(tt,TEST)
except Exception:
    shutil.copy2(backup/"provider.py.v1051",PROVIDER)
    raise
print("v1.0.5.1.1 applied.")
print("Backups written to pre-v10511-backup.")
