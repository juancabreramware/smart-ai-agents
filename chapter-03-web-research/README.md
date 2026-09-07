# Chapter 3 — Research Once, Automate Forever
## Building Self-Learning Web Research Agents

This is the complete runnable implementation for Chapter 3 of **Smart AI Agents — Don't Let Tokens Eat Up Your Budget**.

The project compares two architectures against the same recurring web-research task:

- **Reasoning-First baseline:** every execution retrieves the current page and asks the LLM to understand/extract it again.
- **Smart Agent:** the first execution uses the LLM to discover a reusable extraction procedure, validates it, stores it as a versioned capability, and later executions retrieve fresh data with that deterministic capability. If validation fails after the page changes, the LLM returns, repairs the capability, and a new version is promoted.

The important distinction is this:

```text
We reuse HOW to retrieve the data.
We do not reuse yesterday's data and pretend it is fresh.
```

The repository deliberately does **not** hard-code or recommend a model. Models change faster than technical books. You select a current model via `OPENAI_MODEL`.

### v1.1 — Real-model hardening

v1.1 incorporates what the first real-model run taught us. The deterministic mock had hidden two assumptions that a real model immediately exposed: it may return `per month` when the canonical contract expects `month`, and a learned price recipe may accidentally lose currency evidence. v1.1 adds a **single trusted normalization layer shared by both architectures**, optional separate currency extraction, stronger discovery/repair prompts, visible promotion-failure diagnostics, and regression tests for those cases.

The promotion gates remain strict. We fixed the contract; we did **not** weaken validation.

---

## 1. What you need

### Required for the real controlled experiment

- Python **3.11+**; Python 3.12 is a good choice.
- An OpenAI API account/key.
- A current model name in `OPENAI_MODEL` that supports the **Responses API** and **Structured Outputs**.

### Optional

- A **Serper** API key for live source discovery when you do not already know the official pricing URL.
- Playwright Chromium for JavaScript-rendered live sites.

The reproducible controlled benchmark does **not** require Serper and normally retrieves its local site with ordinary HTTP.

---

## 2. Install on Windows PowerShell

```powershell
cd chapter-03-web-research

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

# Recommended if you will use live sites that need JavaScript rendering:
python -m playwright install chromium

Copy-Item .env.example .env
```

If PowerShell blocks activation for the current process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

---

## 3. Install on macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env
```

---

## 4. Configure `.env`

For real LLM execution:

```dotenv
OPENAI_API_KEY=your-key
OPENAI_MODEL=your-current-model-name
```

No model is recommended in this repository by design. Pick a current model in your account that supports the Responses API and JSON Schema Structured Outputs.

### Cost tracking

Enter the **current** rates for the model you chose:

```dotenv
OPENAI_INPUT_USD_PER_MILLION=0
OPENAI_CACHED_INPUT_USD_PER_MILLION=0
OPENAI_OUTPUT_USD_PER_MILLION=0
```

Leaving these at zero will still run the experiment and measure tokens, but the dollar-cost fields will be zero and break-even cost analysis will not be meaningful.

### Optional Serper

```dotenv
SERPER_API_KEY=your-key
SERPER_ENDPOINT=https://google.serper.dev/search
SERPER_USD_PER_1000_SEARCHES=0
```

Serper is only used when a live vendor has no configured `pricing_url`.

**Never commit `.env`.**

---

## 5. First run: verify everything without spending money

The repository includes a deterministic mock provider. It is not a benchmark and its cost/token numbers are meaningless. It exists so you can verify the entire architecture first.

```powershell
python experiments/full_experiment.py --provider mock --config config/experiment.demo.yaml --reset
```

You should see a lifecycle approximately like:

```text
V1 execution 1
baseline -> REASONING
smart    -> REASONING -> capability v1 promoted

V1 execution 2
baseline -> REASONING
smart    -> DETERMINISTIC -> 0 LLM calls

...

site switches to v2

V2 execution 1
baseline -> REASONING
smart    -> old capability fails validation
         -> RELEARNING
         -> capability v2 promoted

V2 execution 2
smart    -> DETERMINISTIC -> 0 LLM calls
```

Look in:

```text
capabilities/registry/
```

You will see the actual capability JSON files. Open them. That is **Executable Memory** in this experiment.

---

## 6. Run the real controlled demo with OpenAI

```powershell
python experiments/full_experiment.py --provider openai --config config/experiment.demo.yaml --reset
```

The demo config uses only 5 v1 executions and 3 v2 executions so you can watch the system without making your first experience a surprise API bill.

When the implementation is behaving correctly and you are ready for the book benchmark:

```powershell
python experiments/full_experiment.py --provider openai --config config/experiment.full.yaml --reset
```

The full configuration uses:

```text
100 executions on v1
50 executions after switching to v2
```

The baseline therefore makes a paid extraction call on every execution. Review your chosen model's pricing before running the full benchmark.

---

## 7. What the experiment actually does

The controlled site is a tiny local SaaS pricing page called **Northstar Cloud**.

### Site v1

```html
<div class="pricing-card">
    <h2 class="plan-name">Professional</h2>
    <span class="price">$49</span>
    <span class="period">per month</span>
</div>
```

On the first Smart run, the LLM sees the page and produces two things:

1. the current pricing result;
2. a reusable constrained extraction recipe.

A capability looks roughly like:

```json
{
  "container_selector": "div.pricing-card",
  "plan_name": {"selector": "h2.plan-name", "attribute": "text"},
  "displayed_price": {"selector": "span.price", "attribute": "text"},
  "billing_period": {"selector": "span.period", "attribute": "text"}
}
```

The system does **not** trust that just because the model produced it. Promotion requires the deterministic executor to run the recipe and reproduce the validated result.

Later runs fetch the page again and apply the stored procedure with no LLM call.

### Then the experiment breaks the page

Version 2 changes the structure and the prices:

```html
<section data-plan-card="true">
    <h3 class="plan-title">Professional</h3>
    <span data-current-price="$55">$55</span>
</section>
```

The v1 selectors no longer work. Validation detects that the old capability cannot produce the expected current structure. The old capability becomes `DEGRADED`, the model returns, produces a repaired recipe, the new recipe must pass promotion validation, and capability v2 becomes active.

The next run goes back to deterministic execution.

That is the experiment's core claim expressed as code:

```text
Reason -> Learn -> Promote -> Reuse -> Validate -> Fail -> Relearn -> Reuse
```

---

## 8. Why the LLM learns a recipe instead of arbitrary Python

This choice is intentional.

Chapter 3 is trying to prove that reasoning can create **durable procedural capability**. Arbitrary generated Python would add a second major experiment involving sandboxing, shell access, dependency management, security review, and code execution policy.

Here the LLM generates a constrained declarative artifact. A trusted executor interprets it.

```text
LLM discovers procedure
        ↓
procedure becomes constrained data
        ↓
trusted software executes it
        ↓
future reasoning disappears until needed
```

That still implements Artifact Promotion and Executable Memory, without pretending arbitrary model-generated code should get production credentials because it passed a vibe check.

Later chapters can graduate to executable code artifacts when code generation is actually the point of the chapter.

---

## 9. Manual walkthrough

If you want to see each step yourself rather than let the full runner orchestrate it:

### Terminal 1 — start the controlled site

```powershell
python benchmark_site/server.py
```

Open this URL in your browser if you want to see it:

```text
http://127.0.0.1:8765/pricing
```

### Terminal 2 — reset site to v1

```powershell
python experiments/inject_failure.py --version v1
```

Delete old learned capabilities if you want a true cold start:

```powershell
Remove-Item .\capabilities\registry\*.json -ErrorAction SilentlyContinue
```

### Smart run 1

```powershell
python experiments/run_smart.py --provider openai
```

Expected path:

```text
REASONING
```

A v1 capability should appear in `capabilities/registry`.

### Smart run 2

```powershell
python experiments/run_smart.py --provider openai
```

Expected path:

```text
DETERMINISTIC
model_calls=0
```

### Break the world

```powershell
python experiments/inject_failure.py --version v2
```

Refresh the browser. The page has changed.

### Smart run 3

```powershell
python experiments/run_smart.py --provider openai
```

Expected path:

```text
RELEARNING
```

You should now see capability v1 preserved as degraded/disabled history and capability v2 active.

### Smart run 4

```powershell
python experiments/run_smart.py --provider openai
```

Expected:

```text
DETERMINISTIC
model_calls=0
```

---

## 10. Run the Reasoning-First baseline manually

```powershell
python experiments/run_baseline.py --provider openai
```

Run it again:

```powershell
python experiments/run_baseline.py --provider openai
```

And again.

That repetition is the point. The baseline does not retain a cross-run procedural capability.

---

## 11. Benchmark artifacts

Each experiment writes to:

```text
benchmark/results/<experiment-id>/
```

Files include:

```text
manifest.json
executions.jsonl
summary.json
summary.md
cumulative_cost.png
llm_calls_by_execution.png
latency_by_architecture.png
```

### `executions.jsonl`

This is the important one. Every line records one execution, including:

- architecture
- execution path
- capability ID/version
- model calls
- input tokens
- cached input tokens
- output tokens
- search/browser/HTTP calls
- measured cost
- latency
- validation result
- correctness score
- fallback/relearning events

Do not throw the raw ledger away after creating a pretty graph. Pretty graphs cannot answer uncomfortable questions later; raw data can.

---

## 12. Pricing and reproducibility

The manifest records:

- provider name
- `OPENAI_MODEL`
- Python/platform information
- Git commit when available
- experiment configuration
- the model/tool pricing snapshot you entered

This separates two things that should never be conflated:

```text
MEASURED USAGE
    from
PRICE APPLIED TO THAT USAGE
```

If pricing changes six months later, you can recalculate economics from the original measured tokens without rerunning the experiment.

---

## 13. Optional live-web research

Copy:

```text
config/live_vendors.example.yaml
```

to:

```text
config/live_vendors.yaml
```

Add three public SaaS vendors.

If you know each official pricing URL, provide it. That eliminates the search variable.

If you omit `pricing_url`, configure Serper and provide a search query. The code:

1. searches with Serper;
2. filters results to the official domain **before** spending model intelligence;
3. asks the model to choose the likely official pricing page among those candidates;
4. fetches the page;
5. learns/reuses a capability.

Run:

```powershell
python experiments/live_research.py --provider openai --architecture smart --config config/live_vendors.yaml
```

Or baseline:

```powershell
python experiments/live_research.py --provider openai --architecture baseline --config config/live_vendors.yaml
```

### Live-site warning

The controlled site is the reproducible benchmark. Live sites are realism tests. They can change, block automation, geo-personalize content, require consent flows, or have terms that restrict automated access. Respect site terms, robots policies, rate limits, authentication boundaries, and applicable law.

This chapter is about architectural reuse, not seeing how quickly we can get an IP address banned.

---

## 14. Test suite

Tests do not call paid APIs:

```powershell
pytest -q
```

They verify, among other things:

- the v1 learned recipe extracts the v1 ground truth;
- the v1 recipe fails against v2;
- the v2 recipe extracts v2 correctly;
- capability versions are retained and only the latest promoted version is active;
- ground-truth validation catches wrong prices.

---

## 15. Project layout

```text
chapter-03-web-research/
│
├── README.md
├── requirements.txt
├── .env.example
│
├── config/
│   ├── experiment.demo.yaml
│   ├── experiment.full.yaml
│   └── live_vendors.example.yaml
│
├── prompts/
│   ├── baseline-research-v1.txt
│   ├── source-selection-v1.txt
│   ├── discovery-v1.txt
│   └── repair-v1.txt
│
├── smart_agent/
│   ├── models.py
│   ├── settings.py
│   ├── model_provider.py
│   ├── search_provider.py
│   ├── fetcher.py
│   ├── extractor.py
│   ├── validator.py
│   ├── registry.py
│   ├── telemetry.py
│   ├── common.py
│   ├── baseline_agent.py
│   └── smart_agent.py
│
├── capabilities/
│   └── registry/
│
├── benchmark_site/
│   ├── server.py
│   ├── current_version.txt
│   ├── v1/pricing.html
│   ├── v2/pricing.html
│   ├── v3/pricing.html
│   └── ground_truth/
│
├── experiments/
│   ├── run_baseline.py
│   ├── run_smart.py
│   ├── inject_failure.py
│   ├── full_experiment.py
│   └── live_research.py
│
├── benchmark/
│   └── report.py
│
└── tests/
```

---

## 16. The experimental standard

The mock run proves the plumbing.

A Chapter 3 result suitable for the manuscript should use:

- `--provider openai`
- a recorded current `OPENAI_MODEL`
- current pricing entered before the run
- a clean capability registry (`--reset`)
- committed prompt versions
- the full manifest
- the raw ledger
- the generated benchmark report

If the Smart Agent costs more, fails more, or breaks even after an absurd number of executions, keep the result. The experiment is supposed to discover the economics, not audition for the marketing department.

The promise to the reader is simple:

> **You do not have to believe the architecture. Run it.**
