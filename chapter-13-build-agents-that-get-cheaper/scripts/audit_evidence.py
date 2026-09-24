from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import argparse,json
from pathlib import Path
from src.workload import build,workload_hash
from src.scoring import ground_truth
from src.models import Request
from src.accounting import provider_cost_micro
from src.contracts import CONTRACT_VERSION,contract_manifest,hash_json
from src.capabilities import POLICY_VERSION,POLICY_HASH

p=argparse.ArgumentParser(); p.add_argument("--evidence-dir",required=True); a=p.parse_args()
d=Path(a.evidence_dir); errors=[]; recomputed={}
manifest=json.loads((d/"manifest.json").read_text())
if manifest["canonical_workload_hash"]!=workload_hash(build()): errors.append("canonical workload hash mismatch")
if manifest["policy_version"]!=POLICY_VERSION or manifest["policy_hash"]!=POLICY_HASH: errors.append("policy provenance mismatch")
if manifest["public_contract_version"]!=CONTRACT_VERSION or manifest["public_contract_hash"]!=hash_json(contract_manifest()): errors.append("public contract provenance mismatch")

def read_jsonl(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]

for name in ["stateless_reason","episodic_reuse","compounding_smart"]:
    rows=read_jsonl(d/f"{name}_ledger.jsonl")
    for x in rows:
        r=Request(x["request_id"],x["sequence"],x["wave"],x["family"],x["version"],x["payload"],x["reasoning_required"])
        expected=ground_truth(r).value
        if x["expected"]!=expected: errors.append(f"{name}:{x['request_id']}: expected mismatch")
        if x["correct"]!=(x["answer"]==expected): errors.append(f"{name}:{x['request_id']}: correctness mismatch")
        if x["stale_reuse_error"]!=(x["route"]=="deterministic_reuse" and x["answer"]!=expected):
            errors.append(f"{name}:{x['request_id']}: stale reuse mismatch")
    req=len(rows); correct=sum(x["correct"] for x in rows); calls=sum(x["llm_called"] for x in rows)
    inp=sum(x["input_tokens"] for x in rows); out=sum(x["output_tokens"] for x in rows)
    recomputed[name]={"requests":req,"correct":correct,"accuracy":correct/req,"llm_calls":calls,
        "input_tokens":inp,"output_tokens":out,"total_tokens":inp+out,"provider_cost_micro":provider_cost_micro(inp,out),
        "deterministic_reuses":sum(x["route"]=="deterministic_reuse" for x in rows),
        "stale_reuse_errors":sum(x["stale_reuse_error"] for x in rows)}

# Persistence/reset methodology checks from event ledgers.
epi=read_jsonl(d/"episodic_reuse_capability_events.jsonl")
comp=read_jsonl(d/"compounding_smart_capability_events.jsonl")

# Only require wave-specific events for waves actually exercised by this
# evidence set. A short real-provider demo may intentionally contain only
# Wave 1, while the canonical benchmark contains all four waves.
observed_waves=sorted({
    x["wave"]
    for name in ["stateless_reason","episodic_reuse","compounding_smart"]
    for x in read_jsonl(d/f"{name}_ledger.jsonl")
})

for w in [2,3,4]:
    if w in observed_waves and not any(e["event"]=="RESET" and e["wave"]==w for e in epi):
        errors.append(f"episodic reset missing at wave {w}")

if any(e["event"]=="RESET" for e in comp):
    errors.append("compounding registry was reset")

# Drifted families must show invalidation only when Wave 3 was actually
# exercised by this evidence set.
if 3 in observed_waves:
    for fam in ["invoice","supplier","order"]:
        inv=[e for e in comp if e["family"]==fam and e["event"]=="INVALIDATE" and e["wave"]==3]
        if not inv:
            errors.append(f"compounding missing wave-3 invalidation for {fam}")

reported=json.loads((d/"summary.json").read_text())
for name,r in recomputed.items():
    for k in ["requests","correct","accuracy","llm_calls","input_tokens","output_tokens","total_tokens","provider_cost_micro","deterministic_reuses","stale_reuse_errors"]:
        if reported[name][k]!=r[k]: errors.append(f"{name}: summary mismatch {k}")

# Obvious future-leak field names must never appear in request ledgers/events.
bad=("future_","remaining_requests","next_drift","benchmark_remaining")
for path in d.glob("*.jsonl"):
    if path.name=="ground_truth.jsonl": continue
    txt=path.read_text(encoding="utf-8").lower()
    for token in bad:
        if token in txt: errors.append(f"{path.name}: prohibited future-leak token {token}")

result={"passed":not errors,"errors":errors,"recomputed":recomputed}
(d/"audit.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
print(json.dumps(result,indent=2))
raise SystemExit(0 if not errors else 1)

