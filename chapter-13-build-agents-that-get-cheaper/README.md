# Chapter 13 - Build Agents That Get Cheaper

Reference implementation for Chapter 13 of **Smart AI Agents - Don't Let Tokens Eat Up Your Budget**.

This project implements the frozen Chapter 13 Experimental Specification v1.0:

- 240 requests per architecture
- four 60-request waves: Learn, Reuse, Drift, Mature + Novel
- eight operational families
- three architectures:
  - Stateless Reason
  - Episodic Reuse
  - Compounding Smart Agent
- persistent validated capability registry for Compounding
- per-wave marginal LLM calls, tokens, and provider cost
- selective invalidation under controlled drift
- late-arriving novel families
- independent evidence audit
- canonical-run confirmation gate
- immutable evidence ZIP freeze

## Safety boundary

The LLM never generates or executes arbitrary Python, SQL, shell, network code, `eval`, or `exec`.
It returns a structured answer plus an operation selected from a closed allowlist. Trusted deterministic
software owns compatibility, validation, promotion, invalidation, registry mutation, and execution.

## Windows / PowerShell

```powershell
cd C:\applications\book-smart-ai-agents-chapter-code\chapter-13-build-agents-that-get-cheaper

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

python -m pytest -q
python .\scripts\run_mock_benchmark.py
python .\scripts\audit_evidence.py --evidence-dir .\evidence\benchmark-mock-v1
```

### Small real-provider demo

Set your API key in the environment. Do not put it in source control.

```powershell
$env:OPENAI_API_KEY="YOUR_KEY"
$env:CH13_PROVIDER="openai"
$env:CH13_MODEL="gpt-5-mini"

python .\scripts\run_real_demo.py
python .\scripts\audit_evidence.py --evidence-dir .\evidence\demo-real-v1
```

### Canonical real benchmark

Do this only after mock tests, methodology review, provider-boundary review, and the real demo are clean.

```powershell
$env:OPENAI_API_KEY="YOUR_KEY"
$env:CH13_PROVIDER="openai"
$env:CH13_MODEL="gpt-5-mini"
$env:CH13_CONFIRM_CANONICAL="YES"

python .\scripts\run_real_benchmark.py
python .\scripts\audit_evidence.py --evidence-dir .\evidence\benchmark-real-v1
python .\scripts\freeze_evidence.py --evidence-dir .\evidence\benchmark-real-v1
```

## Important

A successful implementation is **not** evidence that the Compounding architecture will win.
Do not change workload composition, drift locations, promotion rules, or accounting after seeing a canonical result.
If a material methodological change is required, version the specification and benchmark.

## v1.0.0 frozen implementation metadata

- canonical requests: 240
- canonical workload SHA-256: `b5f82e3ff270aff7edc9ee9e36e9f732befc1a5ed161bd79e509b3597f166847`
- public contract SHA-256: `10e57f3758ee8ed88777c3d58086b0d9c8b9e950b6a88e9f3642681b1c9224b3`
- capability policy SHA-256: `70c1eab22c6273df364f69183b80242a662210cabc238c566cc1e2c56e896bfc`
- mock validation: 23 tests passed
- mock evidence audit: PASS
- no real-provider benchmark has been run by this package
