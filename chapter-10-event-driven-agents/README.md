# Chapter 10 - Event-Driven Agents

Reference implementation for Chapter 10 of **Smart AI Agents - Don't Let Tokens Eat Up Your Budget**.

Chapter title: **Don't Spend Tokens Watching Nothing Happen**  
Subtitle: **Building Event-Driven Agents That Reason Only When Something Changes**

This repository implements the experimental contract defined in Chapter 10 Experimental Specification v1.0.

## Architectures

- **Baseline** - invokes the reasoning provider for every observation.
- **Smart** - acquires validated Event Sentinels, evaluates known observations deterministically, selectively invalidates on V2 drift, and calls the provider only for acquisition, reasoning-required events, and relearning.
- **Naive** - low-call unsafe control that lacks Smart's contract-aware drift protections.

## Important

The default `mock` provider is deterministic and costs $0. It exists to validate routing, evidence, audit logic, and workload integrity before any paid real-model run.

The implementation deliberately does **not** hard-code benchmark results. Canonical results must come from a frozen real-model run followed by the independent audit and evidence freeze.

## Quick start

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

python -m pytest -q
python .\scripts\run_mock_benchmark.py
python .\scripts\audit_evidence.py --evidence-dir .\evidence\mock
python .\scripts\freeze_evidence.py --evidence-dir .\evidence\mock
```

Real-model demo (requires `OPENAI_API_KEY` in the environment):

```powershell
$env:CH10_PROVIDER="openai"
$env:CH10_MODEL="gpt-5-mini"
python .\scripts\run_real_demo.py
python .\scripts\audit_evidence.py --evidence-dir .\evidence\real-demo
```

Canonical real benchmark:

```powershell
$env:CH10_PROVIDER="openai"
$env:CH10_MODEL="gpt-5-mini"
python .\scripts\run_real_benchmark.py
python .\scripts\audit_evidence.py --evidence-dir .\evidence\benchmark-real-v1
python .\scripts\freeze_evidence.py --evidence-dir .\evidence\benchmark-real-v1
```

Do not publish quantitative Chapter 10 claims until the canonical real benchmark audit passes and the evidence ZIP/hash are frozen.
