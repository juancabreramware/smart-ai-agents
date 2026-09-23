from __future__ import annotations
import csv, json, hashlib
from dataclasses import asdict
from pathlib import Path
from .models import EvidenceRow, Observation

FIELDS=list(EvidenceRow.__dataclass_fields__.keys())

def write_rows(path: Path, rows: list[EvidenceRow]):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS)
        w.writeheader()
        for r in rows: w.writerow(r.as_dict())

def write_json(path: Path, obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str),encoding="utf-8")

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def summarize(rows: list[EvidenceRow]) -> dict:
    n=len(rows)
    calls=sum(r.llm_called for r in rows)
    correct=sum(r.decision_correct for r in rows)
    return {
        "observations":n,
        "correct":correct,
        "accuracy": correct/n if n else 0,
        "llm_calls":calls,
        "llm_calls_avoided_vs_150":150-calls if n==150 else None,
        "input_tokens":sum(r.input_tokens for r in rows),
        "output_tokens":sum(r.output_tokens for r in rows),
        "measured_llm_cost_usd":round(sum(r.measured_cost_usd for r in rows),9),
        "false_positives":sum(r.false_positive for r in rows),
        "false_negatives":sum(r.false_negative for r in rows),
        "stale_reuse":sum(r.stale_reuse for r in rows),
        "duplicates":sum(r.duplicate_action for r in rows),
        "routes":{route:sum(r.route==route for r in rows) for route in sorted(set(r.route for r in rows))},
    }
