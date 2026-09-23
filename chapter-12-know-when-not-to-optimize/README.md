# Chapter 12 — Know When NOT to Optimize

Companion implementation for **Smart AI Agents — Don't Let Tokens Eat Up Your Budget**.

This repository implements Experimental Specification v1.0. It compares:

1. **Always Reason** — LLM on every request.
2. **Always Optimize** — promote every technically eligible family as soon as possible, ignoring payback.
3. **Smart Selective Optimizer** — deterministic `PROMOTE / DEFER / REASON_ONLY` policy using only evidence observed so far.

The canonical workload is exactly **180 requests**, 30 for each of six task families. The optimizer never receives hidden future counts or future drift events. Reusable capabilities execute through a closed trusted runtime; the project never executes arbitrary LLM-generated Python.

## Windows / PowerShell

```powershell
cd C:\applications\book-smart-ai-agents-chapter-code\chapter-12-know-when-not-to-optimize

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m pytest -q
python .\scripts\run_mock_benchmark.py
python .\scripts\audit_evidence.py --evidence-dir .\evidence\mock-v1
```

Do **not** run the paid canonical benchmark yet.

## Real demo

The real-provider path uses the OpenAI Responses API and strict JSON Schema output. It uses only the Python standard library at runtime.

```powershell
$env:OPENAI_API_KEY="..."
$env:CH12_PROVIDER="openai"
$env:CH12_MODEL="gpt-5-mini"

python .\scripts\run_real_demo.py
python .\scripts\audit_evidence.py --evidence-dir .\evidence\demo-real-v1
```

The demo is only a provider/integration gate. Its economics are not canonical evidence.

## Canonical real benchmark — intentionally gated

Only after tests, mock regression, demo, and audit are green:

```powershell
$env:CH12_CONFIRM_CANONICAL="YES"
python .\scripts\run_real_benchmark.py
python .\scripts\audit_evidence.py --evidence-dir .\evidence\benchmark-real-v1
python .\scripts\freeze_evidence.py --evidence-dir .\evidence\benchmark-real-v1
```

Run the canonical benchmark once. Do not rerun it merely because the result is less dramatic than expected.

## Cost accounting

Provider token cost and benchmark-assigned optimization overhead are kept separate. Acquisition, validation, maintenance/relearning proxies are experimental accounting assumptions, **not market prices**.

## Safety boundary

This chapter demonstrates constrained reusable capabilities backed by a trusted deterministic runtime. It does not execute arbitrary model-generated code, `eval`, `exec`, shell commands, or unrestricted network operations.
