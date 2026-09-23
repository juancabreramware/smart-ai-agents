from pathlib import Path
import argparse,json,sys,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.runner import summarize
from src.scoring import is_correct
from src.models import Answer
from src.contracts import PUBLIC_OPERATIONAL_CONTRACT_VERSION,public_operational_contract_manifest
p=argparse.ArgumentParser();p.add_argument("--evidence-dir",required=True);a=p.parse_args();d=Path(a.evidence_dir);errors=[];recomputed={}
def read_jsonl(path):return [json.loads(x) for x in path.read_text(encoding="utf8").splitlines() if x.strip()]
def hash_json(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()
truth={x["request_id"]:x for x in read_jsonl(d/"ground_truth.jsonl")}
for name in ["always_reason","always_optimize","smart"]:
    f=d/f"{name}_ledger.jsonl"
    if not f.exists():errors.append(f"missing {f.name}");continue
    rows=read_jsonl(f);recomputed[name]=summarize(rows)
    if len(rows) not in (15,180):errors.append(f"{name}: unexpected row count {len(rows)}")
    for r in rows:
        if r["provider_cost_micro"]<0 or r["optimization_overhead_micro"]<0:errors.append(f"{name}:{r['request_id']} negative cost")
        t=truth.get(r["request_id"])
        if not t:errors.append(f"{name}:{r['request_id']} missing oracle row");continue
        oracle=Answer(t["action"],t["value"]);actual=Answer(r["actual"]["action"],r["actual"]["value"]);independent=is_correct(oracle,actual)
        if independent!=r["correct"]:errors.append(f"{name}:{r['request_id']} correctness flag disagrees with oracle")
summary=json.loads((d/"summary.json").read_text())
if recomputed!=summary:errors.append("summary does not equal ledger recomputation")
manifest=json.loads((d/"manifest.json").read_text());cost_manifest=json.loads((d/"cost_manifest.json").read_text())
if manifest.get("cost_manifest_hash")!=hash_json(cost_manifest.get("assigned_cost_profiles",{})):errors.append("cost manifest hash mismatch")
policy=cost_manifest.get("policy",{})
if manifest.get("policy_hash")!=hash_json(policy):errors.append("policy hash mismatch")
provider_contract=public_operational_contract_manifest()
if manifest.get("provider_contract_version")!=PUBLIC_OPERATIONAL_CONTRACT_VERSION:errors.append("provider contract version mismatch")
if manifest.get("provider_contract_hash")!=hash_json(provider_contract):errors.append("provider contract hash mismatch")
# A post-promotion DEFER/REASON_ONLY decision must never be contradicted by a
# same-sequence RELEARN event.
cases=read_jsonl(d/"optimization_cases.jsonl") if (d/"optimization_cases.jsonl").exists() else []
caps=read_jsonl(d/"capability_events.jsonl") if (d/"capability_events.jsonl").exists() else []
relearn={(x.get("sequence"),x.get("family")) for x in caps if x.get("event")=="RELEARN"}
for e in cases:
    if e.get("post_promotion_reevaluation") and e.get("decision")!="PROMOTE" and (e.get("sequence"),e.get("family")) in relearn:errors.append(f"{e['family']}:{e['sequence']} non-PROMOTE reevaluation contradicted by RELEARN")
# Public workload is the only routing input persisted; reject obvious future-leak fields.
for w in read_jsonl(d/"workload.jsonl"):
    forbidden={"future_count","remaining_requests","next_drift","future_drift","benchmark_remainder"}.intersection(w)
    if forbidden:errors.append(f"{w.get('request_id')} forbidden future metadata: {sorted(forbidden)}")
result={"passed":not errors,"errors":errors,"recomputed":recomputed};(d/"audit.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf8");print(json.dumps(result,indent=2));raise SystemExit(0 if not errors else 1)

