# Chapter 9 — Ask Once, Query Forever

Reference implementation for the Chapter 9 evidence-first experiment in **Smart AI Agents — Don't Let Tokens Eat Up Your Budget**.

The benchmark compares:
- **Baseline** — asks the LLM to produce a query capability for every request.
- **Smart** — learns a validated parameterized query capability, reuses it deterministically, and selectively relearns after V2 drift.
- **Naive** — reuses the first query template by coarse family match and intentionally omits Smart drift protections.

## Quick start (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python scripts/build_database.py
pytest -q
python scripts/validate_openai_schemas.py
python scripts/run_demo.py --planner mock --output evidence\demo-mock-v1
python scripts/audit_evidence.py evidence\demo-mock-v1 --expected-count 15
```

Real-model integration (requires `OPENAI_API_KEY`):

```powershell
python scripts/run_demo.py --planner openai --output evidence\demo-real-v1
```

Do not run the canonical real benchmark until the demo is clean and the experiment is frozen.

```powershell
python scripts/run_benchmark.py --planner openai --output evidenceenchmark-real-v1
python scripts/audit_evidence.py evidenceenchmark-real-v1
python scripts/freeze_evidence.py evidenceenchmark-real-v1 --name chapter-09-full-real-v1.0-evidence.zip
```

The local benchmark uses SQLite as a deterministic, zero-service execution harness while keeping SQL deliberately PostgreSQL-compatible (named parameters are compiled to driver parameters). Production adapters can replace the executor without changing the experimental architecture. Canonical runs must record the actual database engine in the manifest.
