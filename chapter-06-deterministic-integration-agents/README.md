# Chapter 6 - Call the API, Not the LLM
## Building Deterministic Integration Agents

This directory is the runnable companion implementation for Chapter 6 of **Smart AI Agents - Don't Let Tokens Eat Up Your Budget**.

The experiment asks a narrow question: **Why ask an LLM to rediscover how to call an API after the system has already learned, tested, and validated the integration?**

The repository compares three architectures over the same fixed workload:

- **Baseline Integration Agent** - GPT-5.6 plans every request.
- **Smart Integration Agent** - retrieves a validated executable API capability first and calls GPT-5.6 only for acquisition, reasoning-required requests, or contract-triggered repair.
- **Naive Integration Cache** - reuses prior plans by operation family without current-contract safeguards. This is an intentionally unsafe ablation.

## Scenario

HarborPoint Distribution Group is fictional. Six deterministic local API simulators represent CRM, Support, Billing, Messaging, Inventory, and Identity systems. No external business APIs are required.

## Contract change

The benchmark starts on Contract V1 and then switches to V2:

- Support `create_ticket` gains required `category`.
- Billing `apply_credit` changes `amount` to `amount_cents`; high-value credits require `approval_code`.
- Inventory `reserve_sku` changes `warehouse_id` to `location_id` and requires `idempotency_key`.
- CRM, Messaging, Identity, and unrelated operations remain unchanged.

Smart must selectively invalidate only affected capabilities, relearn them, promote new versions, and then return to deterministic reuse.

## Setup

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

For real-model runs, add `OPENAI_API_KEY` to `.env`. The code defaults to `OPENAI_MODEL=gpt-5.6`.

## Run the deterministic tests

```bash
python -m unittest discover -s tests -v
```

## Mock demo - no API spend

```bash
python -m experiments.runner `
  --mode mock `
  --workload workloads/demo.json `
  --architecture all `
  --outdir results/demo-mock
```

## Full 150-request mock benchmark - no API spend

```bash
python -m experiments.runner `
  --mode mock `
  --workload workloads/full_150.json `
  --architecture all `
  --outdir results/full-mock
```

## Real 15-request hardening gate

Do not jump directly to the paid 150-request benchmark. First run:

```bash
python -m experiments.runner `
  --mode real `
  --workload workloads/demo.json `
  --architecture all `
  --outdir results/demo-real-v1.0
```

Audit every model-generated capability. If the real model exposes a missing validation rule, fix the validator and add a regression test before continuing.

## Real 150-request publication benchmark

Only after the real demo passes:

```bash
python -m experiments.runner `
  --mode real `
  --workload workloads/full_150.json `
  --architecture all `
  --outdir results/full-real-v1.0
```

Then audit:

```bash
python -m experiments.audit results/full-real-v1.0
```

Freeze that directory into an immutable evidence ZIP and record its SHA-256 before writing publication claims.

## Evidence files

Each run writes:

- `baseline.jsonl`
- `smart.jsonl`
- `naive.jsonl`
- `smart_registry.json`
- `smart_invalidated.json`
- `summary.json`
- `manifest.json`

The raw JSONL ledgers are the source of truth. Do not overwrite a real benchmark to make later instrumentation fixes look cleaner.

## OpenAI API implementation

`providers/planner.py` uses the Responses API with JSON Schema Structured Outputs. The model receives the active API contract plus the documented operation-family entry from `catalog/operation_catalog.json`, so the experiment measures repeated integration compilation rather than undocumented guessing. It loads `.env` via `python-dotenv`, reads actual usage returned by the API, records cached input tokens when present, and computes model cost from the frozen environment pricing variables.

## Important experimental boundary

The deterministic `canonical_plan()` function is ground truth for this controlled experiment. It represents the policy/contract validator. A production system would encode equivalent API contracts, generated client schemas, integration tests, approvals, and business rules rather than relying on a benchmark oracle.

## What success looks like

The final real benchmark should demonstrate, rather than assume:

1. Baseline and Smart preserve audited correctness.
2. Smart makes materially fewer GPT-5.6 calls.
3. Compatible capabilities execute with zero LLM calls.
4. V2 contract drift selectively invalidates affected capabilities.
5. GPT-5.6 repairs invalidated integrations.
6. repaired capabilities are promoted as new versions and reused deterministically.
7. Naive contract-unaware reuse is cheaper but produces stale failures.

No numerical savings claim belongs in Chapter 6 until the real evidence is frozen and independently audited.
