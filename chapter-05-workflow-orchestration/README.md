# Chapter 5 — Workflow Orchestration Experiment v1.0

Companion implementation for **Smart AI Agents — Chapter 5: Stop Replanning Known Work: Workflows, Orchestration, and Reusable Reasoning**.

The controlled scenario uses the fictional **Northstar Manufacturing Group** internal IT service desk. It has no connection to any real company, employer, SaaS portfolio, or production system.

This project compares three architectures:

1. **Baseline Planning Agent** — asks the LLM to plan every request.
2. **Smart Workflow Agent** — acquires, validates, promotes, reuses, invalidates, and relearns versioned executable workflow capabilities.
3. **Naive Plan Cache** — intentionally unsafe ablation that reuses plans without policy-version or dependency validation.

All side effects run against deterministic local enterprise-system simulators. The LLM plans; deterministic code executes.

---

## 1. Requirements

Use:

- Windows PowerShell
- Python 3.12 or newer
- An OpenAI API key for the real GPT-5.6 runs
- Internet access for the real-model runs

Check Python:

```powershell
python --version
```

You should see Python 3.12+.

This project has also been tested successfully with Python 3.13.

---

## 2. Open the Chapter 5 Project Folder

Example:

```powershell
cd C:\applications\book-smart-ai-agents-chapter-code\chapter-05-workflow-orchestration
```

All commands below assume you are running them from the project root.

---

## 3. Create a Python Virtual Environment

Create the virtual environment once:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

After activation, your PowerShell prompt should begin with something similar to:

```text
(.venv)
```

If PowerShell blocks activation because of the execution policy, run this once in the current PowerShell session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

Whenever you open a new PowerShell window later, return to the project folder and reactivate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## 4. Install the Python Dependencies

Upgrade `pip`:

```powershell
python -m pip install --upgrade pip
```

Install the project dependencies:

```powershell
pip install -r requirements.txt
```

The project requires the OpenAI Python SDK and `python-dotenv`.

Make sure `requirements.txt` contains:

```text
openai>=1.100.0
python-dotenv>=1.0.0
```

If you add `python-dotenv`, rerun:

```powershell
pip install -r requirements.txt
```

---

## 5. Configure the `.env` File

The project root should contain:

```text
.env.example
```

Create a local `.env` file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and add your real OpenAI API key.

Example:

```text
OPENAI_API_KEY=YOUR_ACTUAL_OPENAI_API_KEY
OPENAI_MODEL=gpt-5.6
OPENAI_REASONING_EFFORT=medium
OPENAI_TIMEOUT_SECONDS=180
```

Do **not** commit `.env` to GitHub.

The included `.gitignore` should already exclude it.

### Important

Python does not automatically read `.env` files.

`providers\planner.py` must load the file with `python-dotenv`.

Near the top of:

```text
providers\planner.py
```

make sure the imports include:

```python
from dotenv import load_dotenv

load_dotenv()
```

A typical beginning of the file should look like:

```python
from __future__ import annotations

import json
import os
import time

from dotenv import load_dotenv

load_dotenv()
```

Without this, the program may fail with:

```text
openai.OpenAIError: The api_key client option must be set...
```

even when the key exists in `.env`.

---

## 6. Verify That the API Key Loads

Run this command:

```powershell
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('OPENAI_API_KEY is set' if os.getenv('OPENAI_API_KEY') else 'OPENAI_API_KEY is NOT set')"
```

Expected result:

```text
OPENAI_API_KEY is set
```

This confirms the key exists without printing the key itself.

Do not paste your actual API key into logs, screenshots, GitHub, or book evidence.

---

## 7. Run the Test Suite

Before running any experiment, run:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 12 tests
OK
```

The tests validate the core experiment mechanics, including:

- Engineering V1 workflow behavior
- Engineering V2 MFA-before-repository-access rule
- Finance V2 security-awareness rule
- stale-plan rejection
- Smart Agent acquisition and reuse
- selective invalidation
- relearning after policy change
- naive stale-cache failure
- contractor expiration
- reasoning-required requests not being promoted
- exact 150-request workload size
- workload-class distribution

Do not continue to paid GPT-5.6 runs if the tests fail.

---

## 8. Run the Zero-Cost 15-Request Demo

This uses the deterministic mock planner and makes no OpenAI API calls.

```powershell
python -m experiments.runner `
    --mode mock `
    --workload workloads/demo.json `
    --architecture all `
    --outdir results/demo-mock
```

Expected output directory:

```text
results\demo-mock
```

The demo exercises:

- initial workflow acquisition
- deterministic reuse
- V1 behavior
- V2 policy transition
- selective invalidation
- relearning
- reuse of the repaired capability
- unchanged workflows that should remain reusable
- naive stale-plan behavior

---

## 9. Run the Zero-Cost Full 150-Request Validation

Before spending money on the real model, validate the complete frozen workload using the mock planner:

```powershell
python -m experiments.runner `
    --mode mock `
    --workload workloads/full_150.json `
    --architecture all `
    --outdir results/full-mock
```

This executes the same 150 frozen requests against:

```text
Baseline
Smart
Naive
```

This is only an architecture validation.

**Do not use mock token, cost, latency, or savings values in the book.**

---

## 10. Run the Real GPT-5.6 15-Request Demo

Only do this after:

```text
12/12 tests pass
mock demo passes
mock full workload passes
OPENAI_API_KEY loads successfully
```

Run:

```powershell
python -m experiments.runner `
    --mode real `
    --workload workloads/demo.json `
    --architecture all `
    --outdir results/demo-real
```

This is the first paid GPT-5.6 experiment.

The output directory should contain files similar to:

```text
results\demo-real\
    baseline.jsonl
    smart.jsonl
    naive.jsonl
    summary.json
    smart_registry.json
```

After this run, **stop**.

Do not immediately run the full paid benchmark.

The real demo must first be inspected for:

- GPT-5.6 plan quality
- schema compliance
- strict validator behavior
- Baseline correctness
- Smart acquisition
- Smart deterministic reuse
- V1 → V2 invalidation
- Smart relearning
- Smart capability promotion
- unchanged-capability survival
- Naive stale reuse
- token usage
- measured cost
- latency
- any model-output edge cases

If anything needs hardening, fix it before the full benchmark.

---

## 11. What the V1 → V2 Policy Change Tests

The experiment begins with:

```text
policy_version = 1
```

For Engineering onboarding, V1 allows repository access after source-control account creation.

Later the environment changes to:

```text
policy_version = 2
```

Under V2:

```text
MFA enrollment must be completed
before repository access is granted.
```

Finance also gains a new security-awareness requirement.

Several other workflows remain unchanged.

This allows the experiment to test whether the Smart Agent performs **selective invalidation** rather than deleting everything it has learned.

The expected Smart Agent lifecycle is:

```text
Engineering onboarding request
        ↓
No capability exists
        ↓
GPT-5.6 plans workflow
        ↓
Validate
        ↓
Execute
        ↓
Promote engineering_onboarding_v1
        ↓
Future compatible requests
        ↓
Deterministic reuse
        ↓
Policy V2 arrives
        ↓
V1 capability no longer valid
        ↓
Invalidate affected capability
        ↓
Return to GPT-5.6
        ↓
Replan
        ↓
Validate
        ↓
Execute
        ↓
Promote engineering_onboarding_v2
        ↓
Future requests reuse v2
```

Meanwhile, an unchanged capability such as Sales onboarding should remain valid.

---

## 12. Architecture Behavior

### Baseline Planning Agent

The Baseline agent intentionally replans every request:

```text
Request
   ↓
GPT-5.6
   ↓
Generate workflow
   ↓
Validate
   ↓
Execute deterministically
```

It does not reuse previous workflow plans.

### Smart Workflow Agent

The Smart Agent first attempts to resolve a validated capability:

```text
Request
   ↓
Normalize
   ↓
Capability Registry
   ↓
Compatible validated workflow?
   ├── YES → Validate current contracts → Execute deterministically
   │
   └── NO  → GPT-5.6 planning
                  ↓
               Validate
                  ↓
               Execute
                  ↓
               Promote
```

An LLM-generated workflow is treated as an **untrusted artifact** until it passes validation.

### Naive Plan Cache

The Naive architecture intentionally omits important safety mechanisms.

It caches a previous workflow and reuses it without sufficient policy/version validation.

It exists as an ablation experiment.

Its purpose is to test:

> High LLM avoidance does not necessarily mean good architecture.

---

## 13. Real Full Benchmark — DO NOT RUN UNTIL DEMO APPROVAL

The full benchmark uses:

```text
workloads\full_150.json
```

There are exactly:

```text
150 requests per architecture
```

across:

```text
Baseline
Smart
Naive
```

for a total of:

```text
450 architecture executions
```

The first 100 requests use V1 policy.

The final 50 requests use V2 policy.

Do not run the real full benchmark until the real 15-request demo has been reviewed and the implementation has been frozen.

When approved, the command will be:

```powershell
python -m experiments.runner `
    --mode real `
    --workload workloads/full_150.json `
    --architecture all `
    --outdir results/full-real
```

Do not run that command prematurely.

---

## 14. Result Files

Each architecture writes an immutable JSONL ledger.

Typical files:

```text
baseline.jsonl
smart.jsonl
naive.jsonl
summary.json
smart_registry.json
```

Each request records information such as:

```text
request ID
policy version
architecture
workflow family
routing path
capability ID/version
LLM usage
input tokens
cached input tokens
output tokens
measured cost
latency
expected operations
actual operations
audited correctness
invalidations
stale reuse
promotion/relearning behavior
```

These ledgers become the basis of the Chapter 5 benchmark analysis.

---

## 15. Evidence Rules

Do not alter raw benchmark ledgers after a real run.

The correct evidence workflow is:

```text
Run benchmark
    ↓
Preserve raw results
    ↓
Audit evaluator behavior
    ↓
Create reassessment tooling if necessary
    ↓
Never overwrite original ledger
    ↓
Freeze evidence directory
    ↓
Create ZIP
    ↓
Compute SHA-256
```

The final Chapter 5 manuscript must only cite measured results that can be traced to frozen evidence.

---

## 16. Pricing

The runner uses configurable model-pricing environment values.

Before the final paid benchmark, verify the current official OpenAI pricing for the exact model being used.

The current code defaults should not be treated as permanently valid pricing.

For a benchmark, preserve:

```text
benchmark date
model name
input-token price
cached-input price
output-token price
```

inside the evidence manifest.

Never silently reuse old pricing for a later run.

---

## 17. Project Structure

```text
chapter-05-workflow-orchestration/
│
├── baseline/
│   └── planning_agent.py
├── smart_agent/
│   ├── agent.py
│   ├── capability_registry.py
│   └── validation.py
├── naive_cache/
│   └── plan_cache.py
├── providers/
│   └── planner.py
├── environment/
│   └── simulator.py
├── policies/
│   ├── policy_v1.json
│   └── policy_v2.json
├── workflows/
│   ├── schema.py
│   └── ground_truth.py
├── workloads/
│   ├── demo.json
│   └── full_150.json
├── experiments/
│   └── runner.py
├── tests/
│   └── test_workflows.py
├── evidence/
├── results/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 18. Common Problems

### Error: API key is missing

Example:

```text
openai.OpenAIError:
The api_key client option must be set...
```

Check:

```powershell
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('OPENAI_API_KEY is set' if os.getenv('OPENAI_API_KEY') else 'OPENAI_API_KEY is NOT set')"
```

If it says:

```text
OPENAI_API_KEY is NOT set
```

verify `.env` exists in the project root and contains:

```text
OPENAI_API_KEY=...
```

Also verify `providers\planner.py` contains:

```python
from dotenv import load_dotenv
load_dotenv()
```

### Error: `No module named dotenv`

Run:

```powershell
pip install python-dotenv
```

or:

```powershell
pip install -r requirements.txt
```

### Error: `No module named openai`

Run:

```powershell
pip install -r requirements.txt
```

### PowerShell will not activate `.venv`

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Tests fail

Do not run the paid benchmark.

Run:

```powershell
python -m unittest discover -s tests -v
```

and fix the failing deterministic behavior first.

---

## 19. Recommended Chapter 5 Run Sequence

Follow this order exactly:

```text
1. Create virtual environment
2. Activate virtual environment
3. Install requirements
4. Create .env
5. Verify API key loads
6. Run 12 deterministic tests
7. Run mock 15-request demo
8. Run mock 150-request validation
9. Run real GPT-5.6 15-request demo
10. Review real demo
11. Harden implementation if necessary
12. Freeze implementation
13. Run real 150-request × 3 benchmark
14. Audit results
15. Freeze evidence
16. Calculate measured economics
17. Write Chapter 5
18. Update Appendix A
```

The key rule is:

> **Do not write the Chapter 5 benchmark conclusions before the real experiment has produced the evidence.**

---

## 20. Chapter 5 Principle

The experiment is designed around this architectural idea:

> **Reasoning should produce assets, not just answers.**

And the operational rule:

> **Use intelligence to discover the workflow. Use software to preserve it. Return to intelligence when the workflow is no longer valid.**

The objective is not maximum LLM avoidance.

The objective is **maximum safe reuse of validated reasoning**.

---

## 21. Safety and Scope

This repository is a controlled book experiment.

It is **not** production identity-management, employee-access, security, IAM, or HR automation.

Real systems require additional safeguards including authorization/approval controls, transactional execution, rollback/compensation, secrets management, audit logging, concurrency controls, idempotency guarantees, identity verification, human approval for sensitive operations, security review, and regulatory/organizational policy enforcement.

The simulated environment exists only to make the workflow-learning experiment reproducible and measurable.
