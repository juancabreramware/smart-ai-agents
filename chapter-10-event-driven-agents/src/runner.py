from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json, os, platform, sys, uuid
from .agents import BaselineAgent, SmartAgent, NaiveAgent
from .provider import build_provider
from .workload import build_workload, demo_workload, workload_hash
from .evidence import write_rows, write_json, summarize

def run(output_dir: Path, demo: bool=False) -> dict:
    observations=demo_workload() if demo else build_workload()
    whash=workload_hash(observations)
    run_id=f"ch10-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    provider=build_provider()
    all_summaries={}
    for name,klass in (("baseline",BaselineAgent),("naive",NaiveAgent),("smart",SmartAgent)):
        agent=klass(provider)
        rows=[agent.process(run_id,o,whash) for o in observations]
        write_rows(output_dir/f"{name}.csv",rows)
        all_summaries[name]=summarize(rows)
    manifest={
        "run_id":run_id,
        "mode":"demo" if demo else "canonical",
        "provider":provider.name,
        "model":provider.model,
        "python":sys.version,
        "platform":platform.platform(),
        "workload_hash":whash,
        "observation_count":len(observations),
        "pricing":{
            "input_usd_per_million":os.getenv("CH10_INPUT_USD_PER_MILLION","0"),
            "output_usd_per_million":os.getenv("CH10_OUTPUT_USD_PER_MILLION","0"),
        },
        "summaries":all_summaries,
    }
    write_json(output_dir/"manifest.json",manifest)
    return manifest
