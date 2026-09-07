# Smart AI Agents
## Companion repository for *Smart AI Agents — Don't Let Tokens Eat Up Your Budget*

This repository contains the working implementations, experiments, benchmarks, and reference material that accompany Juan Cabrera's book **Smart AI Agents — Don't Let Tokens Eat Up Your Budget**.

The book's central engineering principle is simple:

> **An intelligent system should not repeatedly pay an intelligence premium for work it has already learned how to perform.**

The repository grows with the book. Early chapters establish the architecture and terminology; implementation chapters provide runnable experiments that readers can inspect, execute, break, and extend.

## Repository map

| Chapter | Material | Status |
|---|---|---|
| [Chapter 1 — The Trillion-Token Problem](chapter-01-trillion-token-problem/) | Executive framing, economics, and chapter notes | Reference material |
| [Chapter 2 — Smart Agent Architecture](chapter-02-smart-agent-architecture/) | Architecture, terminology, and implementation map | Reference material |
| [Chapter 3 — Web Research](chapter-03-web-research/) | Complete runnable baseline vs. Smart Agent experiment | **Runnable** |

Future chapters will be added as their implementations are completed and validated.

## Start here: Chapter 3

Chapter 3 is the first complete implementation in the book. It compares two architectures against the same recurring SaaS-pricing research workload:

- **Reasoning-First baseline:** fetch fresh data and ask the model to reason again on every execution.
- **Smart Agent:** reason when necessary, promote a validated extraction capability, reuse it deterministically, detect environmental change, and relearn when validation fails.

The controlled experiment deliberately changes the target website after 100 executions so the Smart Agent must detect failure, invoke the model again, repair the capability, promote a new version, and return to deterministic execution.

Go to **[chapter-03-web-research](chapter-03-web-research/)** for installation, walkthroughs, tests, and benchmark commands.

## Verified Chapter 3 benchmark used in the book

The publication benchmark ran **150 executions per architecture** against the controlled workload. Both completed 150/150 successfully with mean correctness of 1.000.

| Metric | Reasoning-First | Smart Agent |
|---|---:|---:|
| LLM calls | 150 | 2 |
| Input tokens | 121,350 | 2,710 |
| Cached input tokens | 0 | 1,344 |
| Output tokens | 29,229 | 1,254 |
| Measured model cost | $1.069980 | $0.031082 |
| Median latency | 2,404.1 ms | 31.4 ms |
| P95 latency | 4,753.8 ms | 61.2 ms |
| Mean correctness | 1.000 | 1.000 |

These are measurements from the controlled Chapter 3 workload, not universal savings claims. See [the benchmark note](docs/chapter-03-verified-benchmark.md) for scope and interpretation.

## Philosophy

The repository follows the same progression as the book:

```text
Reason when necessary
        ↓
Validate what was learned
        ↓
Promote reusable capability
        ↓
Execute deterministically when safe
        ↓
Validate continuously
        ↓
Return to reasoning when the world changes
```

The objective is **not minimum LLM usage**. The objective is **minimum unnecessary LLM usage** while preserving correctness, reliability, and appropriate risk controls.

## Requirements

Chapter-specific requirements live inside each chapter directory. Chapter 3 currently requires Python 3.11+ and can run its test suite and deterministic mock without any paid API key.

## Secrets and generated files

Never commit `.env` files or API credentials. The root `.gitignore` excludes local secrets, virtual environments, Python caches, generated benchmark ledgers/charts, learned runtime capability files, and other local execution artifacts.

The repository intentionally includes `.env.example` files containing placeholders only.

## Book and code versions

The book explains the architecture and reasoning; this repository is the executable companion. Code may evolve as dependencies and model APIs change. Chapter READMEs and changelogs document implementation-specific changes.

## Author

**Juan Cabrera**  
Software engineer and author of *Smart AI Agents — Don't Let Tokens Eat Up Your Budget*.

## License

No open-source license has been added yet. Until a license is selected, copyright remains with the author and the repository is provided for viewing and evaluation. A formal license can be added before broader reuse is invited.
