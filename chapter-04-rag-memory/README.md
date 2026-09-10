# Chapter 4 — Don't Ask the LLM What You Already Know
## RAG, Memory, and Intelligent Reuse

This is the reproducible implementation (v1.1 hardening release) for Chapter 4 of **Smart AI Agents — Don't Let Tokens Eat Up Your Budget**.

It compares three architectures against the same versioned Northstar Cloud knowledge base and fixed workloads:

1. **Baseline RAG** — retrieves evidence and invokes the LLM on every request.
2. **Smart Agent** — checks provenance-backed semantic memory first, validates source freshness and reuse policy, and invokes reasoning only when needed.
3. **Naive Semantic Cache** — an ablation that reuses answers based on similarity without source-version validation, demonstrating why **similarity is not validity**.

## What is locked

The experimental contract is Chapter 4 Experimental Specification v1.0: 100 V1 requests, a deliberate V1→V2 knowledge change, then 50 V2 requests. Changed facts include backup retention, Starter API limits, Enterprise support, EU regions, and annual discount. Unchanged facts remain available to test selective rather than global invalidation.

## Setup

```powershell
py -3.13 -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Default configuration uses a deterministic mock reasoner and local embeddings so the complete lifecycle can be tested without API cost.

```bash
pytest -q
python -m experiments.run --mode demo --verbose
python -m experiments.run --mode full
```

## Real-model run

Set `.env`:

```text
OPENAI_API_KEY=...
CH4_PROVIDER=openai
CH4_EMBEDDINGS=openai
OPENAI_MODEL=gpt-5.6
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Then run the **15-execution real-model demo only**:

```bash
python -m experiments.run --mode demo --verbose
```

This demo uses the fixed 15-request workload (10 requests against V1, then 5 requests against V2) and runs the Baseline RAG, Smart Agent, and Naive Semantic Cache architectures. Inspect the timestamped directory created under `results/` before proceeding.

Verify that the real-model demo shows:

- Baseline RAG reasoning on every request.
- Smart Agent acquisition followed by deterministic memory reuse for safe paraphrases.
- V2 source changes causing `SOURCE_CHANGED`, selective `MEMORY_INVALIDATED`, `RELEARNING`, validation, and promotion of replacement memory.
- Unchanged V1-backed memories remaining reusable after the V2 transition.
- Reasoning-required questions continuing to use the LLM.
- `incorrect_stale_reuse = 0` for the Smart Agent.
- Token counts, latency, and costs coming from the real OpenAI run rather than mock instrumentation.

**Do not run the full paid benchmark until the 15-execution real-model demo ledger and summary have been inspected and the behavior above is confirmed.**

After the real-model demo passes inspection, run the full locked benchmark:

```bash
python -m experiments.run --mode full --verbose
```

The full benchmark executes the fixed **150-request workload per architecture**: 100 requests against V1, followed by the deliberate V1→V2 knowledge change and 50 requests against V2. Preserve the resulting timestamped `results/` directory; its ledger, manifest, summaries, token/cost accounting, latency data, invalidation events, and economics are the evidence used for Chapter 4.

After the full run completes, inspect the generated summary and execution ledger before using any result in the manuscript. Do not rerun merely to obtain more favorable economics; the measured result—positive, negative, or break-even—is the Chapter 4 evidence.

## Result artifacts

Every run creates a timestamped directory under `results/` containing the execution ledger, summary, economics, routing breakdown, stale-memory report, latency summary, token/cost summary, CSV, and run manifest.

Mock-mode token/cost figures are synthetic instrumentation and must **not** be presented as measured OpenAI economics. Real benchmark claims must come from a run with `CH4_PROVIDER=openai` and the pricing recorded in `run_manifest.json`.

## Safety invariant

A semantic match is never sufficient for reuse. A Smart Agent memory must pass intent, provenance, source freshness, evidence, and reuse-policy gates. Changed source facts invalidate only dependent memories.
