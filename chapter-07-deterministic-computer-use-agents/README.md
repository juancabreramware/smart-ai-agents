# Chapter 7 Companion Implementation

## Stop Watching the Screen: Building Deterministic Computer-Use Agents

This repository is the companion implementation for Chapter 7 of **Smart AI Agents — Don't Let Tokens Eat Up Your Budget**.

It implements the Chapter 7 Experimental Specification v1.0 as a reproducible HarborPoint Distribution Group browser-automation experiment with three architectures:

- **Baseline Computer-Use Agent** — asks the LLM to plan every browser task.
- **Smart Computer-Use Agent** — promotes validated UI procedures into versioned executable capabilities and reuses them deterministically while their assumptions remain valid.
- **Naive Replay Agent** — aggressively replays learned procedures without Smart's contract/fingerprint validation, providing the safety counterexample.

The controlled workload deliberately switches the HarborPoint portal from **UI Contract V1 to V2** after request 90. Four operation families change; two remain compatible. That lets the benchmark test selective invalidation instead of simply clearing all learned automation.

> The canonical Chapter 7 claims must come from a real-model, Playwright-backed, audited benchmark. The included mock/simulated validation output is engineering validation only and is **not publication evidence**.

---

## Repository layout

```text
chapter-07-deterministic-computer-use-agents/
  README.md
  pyproject.toml
  docs/
    Smart_AI_Agents_Chapter_7_Experimental_Specification_v1.0.docx
  src/smart_agents_ch7/
    agents/
      baseline.py
      smart.py
      naive.py
    browser/
      executor.py
      simulated_executor.py
      models.py
    capabilities/
      model.py
      registry.py
      compatibility.py
    planner/
      mock.py
      openai_planner.py
      models.py
    portal/
      contracts.py
      server.py
      state.py
    validation/
      plan_validation.py
      ground_truth.py
    benchmark/
      workload.py
      runner.py
      audit.py
      pricing.py
  workloads/
    demo_v1.0.jsonl
    benchmark_v1.0.jsonl
  scripts/
    serve_portal.py
    run_demo.py
    run_benchmark.py
    audit_evidence.py
    freeze_evidence.py
  tests/
  evidence/
```

---

## What is actually learned?

The Smart Agent does **not** cache a screenshot or a raw click trace. It promotes an **Executable UI Capability** containing:

- operation family;
- capability version;
- UI-contract version;
- contract fingerprint;
- start route;
- parameterized browser actions;
- stable selectors;
- required request arguments;
- postcondition identifier;
- validation state;
- reuse/failure counts;
- provenance and invalidation history.

A capability is reused only when its compatibility checks pass. If the active UI contract changes, the affected capability is invalidated, the planner is called again, the replacement plan is validated and executed, and a new capability version is promoted.

---

## HarborPoint operation families

The benchmark contains six recurring browser tasks:

1. `orders.lookup_status`
2. `shipping.update_instructions`
3. `billing.apply_credit`
4. `returns.create_authorization`
5. `customers.update_contact`
6. `inventory.reserve_stock`

### V2 changes

Four families change in V2:

- Shipping moves from `/shipping/update` to `/shipping/details` with new semantic selectors.
- Billing changes the amount field to cents, adds a reason code, and requires an approval code for credits over $100.
- Returns becomes a two-step wizard.
- Inventory changes `warehouse_id` semantics to `location_id` and adds a confirmation step.

Two families intentionally remain compatible:

- `orders.lookup_status`
- `customers.update_contact`

That distinction is essential to the selective-invalidation test.

---

## Frozen candidate workload

The implementation includes the reviewed v1.0 workload files:

```text
workloads/demo_v1.0.jsonl       15 requests
workloads/benchmark_v1.0.jsonl 150 requests
```

Current SHA-256 fingerprints:

```text
benchmark_v1.0.jsonl
74e03f916c6d768e0404ffcc5f1440035b5d431c4f33faa46f4873f909ed4737

demo_v1.0.jsonl
6306320c9217a393b9468440986e571b716e1e0ffb39d0402b997c87edde8533
```

The 150-request workload is deliberately shaped before any real benchmark result exists:

- **Phase A — requests 1–60, V1:** 10 requests per operation family.
- **Phase B — requests 61–90, V1:** 5 requests per family; 18 total are explicitly reasoning-required.
- **Phase C — requests 91–150, V2:** 32 requests exercise changed families and 28 exercise unchanged families.

The workload must not be edited after observing a real benchmark result. A material workload change requires a new experiment version and new hashes.

---

## Setup

### Windows PowerShell

```powershell
cd chapter-07-deterministic-computer-use-agents

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,openai]"
playwright install chromium
```

### macOS / Linux

```bash
cd chapter-07-deterministic-computer-use-agents
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev,openai]'
playwright install chromium
```

---

## 1. Run the tests

```powershell
pytest
```

The ordinary test suite validates workload shape, V1/V2 contract drift, compatibility checks, plan validation, agent routing, stale-reuse behavior, and independent ledger auditing.

The real Playwright integration test is opt-in because some CI/container environments prohibit Chromium from connecting to localhost.

PowerShell:

```powershell
$env:CH7_RUN_PLAYWRIGHT_TESTS="1"
pytest tests/test_browser_integration.py -q
```

macOS / Linux:

```bash
CH7_RUN_PLAYWRIGHT_TESTS=1 pytest tests/test_browser_integration.py -q
```

---

## 2. Inspect the controlled HarborPoint portal

```powershell
python scripts/serve_portal.py --version V1
```

Or:

```powershell
python scripts/serve_portal.py --version V2
```

Open the printed localhost URL in a browser.

---

## 3. Fast local architecture validation

The in-process simulator validates architecture semantics without launching Chromium. It enforces the same active routes/selectors and business-state postconditions, but it is **not** canonical computer-use evidence.

```powershell
python scripts/run_demo.py `
    --planner mock `
    --executor simulated `
    --output evidence\demo-mock
```

Then independently audit the raw ledgers:

```powershell
python scripts/audit_evidence.py evidence\demo-mock
```

The current local mock demo is expected to demonstrate the intended mechanics:

- Baseline: correct on all 15 requests.
- Smart: correct on all 15; acquisition, deterministic reuse, then four V2 relearning events.
- Naive: four stale V2 failures in the four changed operation families.

These numbers are local architecture-validation expectations, **not book benchmark results**.

---

## 4. Full 150-request mock validation

```powershell
python scripts/run_benchmark.py `
    --planner mock `
    --executor simulated `
    --output evidence\mock-validation

python scripts/audit_evidence.py evidence\mock-validation
```

The current deterministic mock validation is intentionally diagnostic. With the frozen v1.0 workload it produces the architecture shape we designed before the real model run:

```text
Baseline
  150 requests
  150 planner calls
  150 correct

Smart
  6  initial acquisitions
  18 reasoning-required executions
  4  relearning events
  122 deterministic reuses
  150 correct
  0 stale reuses

Naive
  6  initial acquisitions
  18 reasoning-required executions
  126 naive reuses
  32 stale/incorrect V2 reuses
```

Again: **do not publish these mock numbers as Chapter 7 evidence.**

---

## 5. Real planner configuration

The real planner uses the OpenAI Responses API with Structured Outputs. The implementation defaults to:

```text
Model: gpt-5.6-sol
Reasoning effort: medium
```

Set the key in your shell:

```powershell
$env:OPENAI_API_KEY="..."
$env:CH7_MODEL="gpt-5.6-sol"
$env:CH7_REASONING_EFFORT="medium"
```

Before the canonical benchmark, pin pricing in the shell or record the current official rates in the experiment manifest. The implementation currently defaults to the GPT-5.6 Sol rates used when this companion build was created:

```powershell
$env:CH7_INPUT_PER_MTOK="4.00"
$env:CH7_CACHED_INPUT_PER_MTOK="0.40"
$env:CH7_OUTPUT_PER_MTOK="20.00"
```

**Verify official pricing immediately before the canonical run.** Do not silently reuse old pricing if provider rates change.

---

## 6. Real 15-request demo — required before the 150-request run

The real demo should use **OpenAI + Playwright**, not the simulated executor:

```powershell
python scripts/run_demo.py `
    --planner openai `
    --executor playwright `
    --output evidence\demo-real-v1

python scripts/audit_evidence.py evidence\demo-real-v1
```

Do not proceed to the canonical run until:

- all 15 requests are present in all three raw ledgers;
- the independent audit passes;
- Smart demonstrates acquisition, safe reuse, selective V2 invalidation, relearning, and later reuse;
- unchanged V2 families remain reusable;
- no real-model schema/selector normalization defect remains;
- Naive is not accidentally receiving Smart's compatibility protections.

If the real demo exposes an implementation bug, fix it, add a regression test, rerun the demo, and version the implementation as needed. Do **not** weaken correctness or alter ground truth to make the model pass.

---

## 7. Canonical real 150-request benchmark

Only after the real demo is accepted:

```powershell
python scripts/run_benchmark.py `
    --planner openai `
    --executor playwright `
    --output evidence\full-real-v1

python scripts/audit_evidence.py evidence\full-real-v1
```

This run is intentionally expensive relative to mock validation: Baseline is designed to make 150 real planning calls. Do not rerun it casually.

Review the raw ledgers and audit before freezing anything.

---

## 8. Freeze accepted evidence

After the real run and independent audit are accepted:

```powershell
python scripts/freeze_evidence.py evidence\full-real-v1 `
    --name chapter-07-full-real-v1.0-evidence.zip
```

The script writes `SHA256SUMS.txt`, creates the ZIP, and prints the evidence ZIP SHA-256.

Once Chapter 7 evidence is declared canonical, later experiments do not replace it silently. They receive a new experiment/evidence version.

---

## Evidence files

Each benchmark output directory contains:

```text
experiment-manifest.json
execution-summary.json
baseline-executions.jsonl
smart-executions.jsonl
naive-executions.jsonl
smart-capability-registry.json
```

After auditing:

```text
audit-report.json
```

After freezing:

```text
SHA256SUMS.txt
chapter-07-...-evidence.zip
```

The raw JSONL ledgers are authoritative. `execution-summary.json` is a convenience view, not the source of truth.

---

## Correctness rules

The benchmark does not treat “the browser clicked the button” as success.

Correctness is audited against HarborPoint's authoritative business state:

- order lookup must return the actual order status;
- shipping instructions must persist exactly;
- credits must appear in the ledger with the right amount and required V2 metadata;
- returns must create the intended RMA state;
- customer contact values must persist;
- inventory reservations must contain the correct SKU, quantity, and location.

A stale plan that fails before mutation is still an incorrect task execution for that request. A stale plan that reaches the wrong state would also be incorrect. The Smart architecture is expected to prevent known-incompatible reuse before executing it.

---

## Why there are two executors

`BrowserExecutor` is the real Playwright implementation required for canonical computer-use evidence.

`SimulatedBrowserExecutor` exists only to make architecture tests fast and deterministic. It enforces the same routes/selectors and mutates the same business state, which makes it useful for unit/regression validation, but it does not prove anything about real browser latency or browser reliability.

Publication claims must therefore be derived from **OpenAI + Playwright** evidence, not mock + simulated evidence.

---

## Publication rule

Do not write Chapter 7 benchmark percentages into the book until the real evidence is frozen.

The chapter's final empirical story must be whatever the raw ledgers and independent audit establish — even if that result is less dramatic than expected.
