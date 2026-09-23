from __future__ import annotations
import csv, json
from pathlib import Path

BOOL={"True":True,"False":False,"true":True,"false":False}

def _rows(path):
    with path.open(encoding="utf-8",newline="") as f: return list(csv.DictReader(f))

def audit(evidence_dir: Path) -> dict:
    manifest=json.loads((evidence_dir/"manifest.json").read_text(encoding="utf-8"))
    names=("baseline","naive","smart")
    data={n:_rows(evidence_dir/f"{n}.csv") for n in names}
    errors=[]
    expected_count=int(manifest["observation_count"])
    for n,rows in data.items():
        if len(rows)!=expected_count: errors.append(f"{n}: expected {expected_count} rows, got {len(rows)}")
        ids=[r["observation_id"] for r in rows]
        if len(ids)!=len(set(ids)): errors.append(f"{n}: duplicate observation IDs")
        if any(r["workload_hash"]!=manifest["workload_hash"] for r in rows): errors.append(f"{n}: workload hash mismatch")
    base_ids=[r["observation_id"] for r in data["baseline"]]
    for n in ("naive","smart"):
        if [r["observation_id"] for r in data[n]]!=base_ids: errors.append(f"{n}: observation order differs from baseline")

    # Smart deterministic rows must contain zero hidden LLM calls.
    for r in data["smart"]:
        if r["route"]=="deterministic_reuse" and BOOL.get(r["llm_called"],False):
            errors.append(f"smart: hidden LLM call in {r['observation_id']}")

    # Recompute headline counts from raw evidence.
    summary={}
    for n,rows in data.items():
        summary[n]={
            "rows":len(rows),
            "correct":sum(BOOL.get(r["decision_correct"],False) for r in rows),
            "llm_calls":sum(BOOL.get(r["llm_called"],False) for r in rows),
            "false_positives":sum(BOOL.get(r["false_positive"],False) for r in rows),
            "false_negatives":sum(BOOL.get(r["false_negative"],False) for r in rows),
            "stale_reuse":sum(BOOL.get(r["stale_reuse"],False) for r in rows),
            "cost_usd":round(sum(float(r["measured_cost_usd"]) for r in rows),9),
        }

    # Canonical design gates. Demo is intentionally smaller.
    if manifest["mode"]=="canonical":
        if summary["baseline"]["llm_calls"]!=150: errors.append("baseline: canonical run must call provider 150 times")
        smart_routes={r["route"] for r in data["smart"]}
        for route in ("initial_acquisition","deterministic_reuse","reasoning_required","relearning"):
            if route not in smart_routes: errors.append(f"smart: missing route {route}")
        if summary["smart"]["stale_reuse"]!=0: errors.append("smart: stale incorrect reuse detected")
        if summary["naive"]["stale_reuse"]<1: errors.append("naive: unsafe control produced no stale-reuse failures; drift test ineffective")

    result={"passed":not errors,"errors":errors,"recomputed":summary,"run_id":manifest["run_id"]}
    (evidence_dir/"audit.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    return result
