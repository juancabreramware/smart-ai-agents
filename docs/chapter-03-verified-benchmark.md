# Chapter 3 — Verified Controlled Benchmark

This note records the benchmark measurements used in Chapter 3 of *Smart AI Agents — Don't Let Tokens Eat Up Your Budget*.

## Workload

Both architectures executed the same controlled SaaS-pricing research workload:

- 100 executions against site version 1
- a deliberate structural/environment change
- 50 executions against site version 2
- 150 total executions per architecture

The Reasoning-First baseline invoked the model on every execution. The Smart Agent used the model for initial capability acquisition and once more for relearning after the deliberate environment change. Reused Smart executions still fetched fresh source data; they did not substitute cached pricing data for current data.

## Measured results

| Metric | Reasoning-First | Smart Agent |
|---|---:|---:|
| Executions | 150 | 150 |
| Successful executions | 150 | 150 |
| Mean correctness | 1.000 | 1.000 |
| LLM calls | 150 | 2 |
| Input tokens | 121,350 | 2,710 |
| Cached input tokens | 0 | 1,344 |
| Output tokens | 29,229 | 1,254 |
| HTTP calls | 150 | 150 |
| Measured model cost | $1.069980 | $0.031082 |
| Median latency | 2,404.1 ms | 31.4 ms |
| P95 latency | 4,753.8 ms | 61.2 ms |

Additional measured economics:

- Capability acquisition: **$0.006630**
- Relearning after the deliberate change: **$0.024452**
- Baseline average model cost per execution: **$0.007133**
- Smart deterministic reused-execution model cost: **$0**
- Cumulative measured model-cost savings: **$1.038898**
- LLM avoidance: **98.7%**
- Simple break-even: **approximately 0.93 reused executions**

## Scope

These values are measurements from this controlled workload. They are not a promise that every agentic workload will achieve the same savings or latency improvement.

The experiment is designed to make the architecture falsifiable: readers can run the included controlled site, baseline, Smart Agent, validation gates, deliberate failure, and relearning lifecycle themselves.

Raw local run ledgers and generated charts are intentionally excluded from source control by `.gitignore`; readers generate their own under `chapter-03-web-research/benchmark/results/`.
