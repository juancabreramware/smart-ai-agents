# Chapter 14 — Prove Every Token You Saved

Implementation companion for **Smart AI Agents — Don't Let Tokens Eat Up Your Budget**.

This project implements the Chapter 14 Experimental Specification v1.0: an evidence-grade
agent-economics benchmark designed to make every savings claim traceable and independently
recomputable.

## Architectures / reports

The benchmark executes the same frozen workload through:

1. **Baseline LLM Every Request** — measured counterfactual.
2. **Smart Agent** — governed deterministic reuse with fresh reasoning on novelty/drift.
3. **Naive Token Dashboard** — intentionally incomplete accounting.
4. **Aggregate Cost Reporter** — correct aggregate provider accounting, weak attribution.
5. **Evidence-Grade Economics Ledger** — request/attempt-level accounting and attribution.

## Safety boundary

The model never receives hidden ground truth, future workload composition, future drift,
remaining horizon, or another architecture's outcomes. The model selects only from a closed
operation allowlist. There is no `eval`, `exec`, arbitrary shell, arbitrary SQL, or arbitrary
network execution.

## Windows / PowerShell

Use `python`, never `py`.

```powershell
cd C:\applications\book-smart-ai-agents-chapter-code\chapter-14-prove-every-token-you-saved
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python .\scripts\run_mock_benchmark.py
python .\scripts\audit_evidence.py --evidence-dir .\evidence\benchmark-mock-v1
```

### Real-provider demo

```powershell
$env:OPENAI_API_KEY="YOUR_ROTATED_KEY"
python .\scripts\run_real_demo.py
python .\scripts\audit_evidence.py --evidence-dir .\evidence\demo-real-v1
```

### Canonical real benchmark

Do this only after tests, mock audit, demo, and manifest review pass.

```powershell
$env:CH14_CONFIRM_CANONICAL="YES"
python .\scripts\run_real_canonical.py
python .\scripts\audit_evidence.py --evidence-dir .\evidence\benchmark-real-v1
python .\scripts\freeze_evidence.py --evidence-dir .\evidence\benchmark-real-v1
```

Do not rerun merely because the measured savings are smaller than expected.

## Important accounting rule

Provider usage is **measured**. Non-provider benchmark costs are **assigned constants** and
are always reported separately. Summary files are derived artifacts; the auditor recomputes
from raw ledgers and manifests.
