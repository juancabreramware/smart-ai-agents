# Chapter 11 — Executable Memory Agents

Implementation for **Smart AI Agents — Chapter 11: Let the LLM Write Itself Out of the Loop**.

Architectures:
- Baseline: LLM on every request.
- Smart: acquire a structured executable capability, validate/promote it, deterministically reuse it while compatible, reason only at explicit semantic boundaries, and selectively relearn after V2 drift.
- Naive: acquire one coarse capability per family and replay it without Smart compatibility/invalidation protections.

Safety: model output is never passed to `eval`, `exec`, a shell, package installer, network client, or arbitrary filesystem API. A model selects a structured operation from a fixed allowlist; the runtime compiles that selection into a deterministic callable.

## Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q

python .\scripts\run_mock_benchmark.py
python .\scripts\audit_evidence.py --evidence-dir .\evidence\mock
```

Before the real demo, pin the model and **current official** API prices:

```powershell
$env:CH11_PROVIDER="openai"
$env:CH11_MODEL="gpt-5-mini"
$env:CH11_INPUT_USD_PER_MILLION="<CURRENT OFFICIAL PRICE>"
$env:CH11_OUTPUT_USD_PER_MILLION="<CURRENT OFFICIAL PRICE>"
python .\scripts\run_real_demo.py
python .\scripts\audit_evidence.py --evidence-dir .\evidence\real-demo
```

Do not run the canonical benchmark until the real demo is reviewed and model/config/pricing are frozen.
