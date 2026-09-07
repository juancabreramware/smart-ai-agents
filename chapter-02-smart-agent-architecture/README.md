# Chapter 2 — Stop Paying Your Agents to Think Twice
## The Smart Agent Architecture

Chapter 2 defines the reference architecture used throughout the implementation chapters.

This directory is intentionally **reference material rather than a premature framework implementation**. Shared production abstractions will be promoted to repository-level components only after multiple chapter implementations demonstrate that the abstraction is genuinely reusable.

## Two execution planes

### Intelligence Plane
Used for novelty, ambiguity, planning, discovery, failure diagnosis, capability generation and repair, and semantic judgment.

### Execution Plane
Used for known operations that can be performed through deterministic software: APIs, SQL, browser workflows, parsers, rules, state machines, and transforms.

## Reference components

1. Request Normalizer
2. Capability Resolver
3. Execution Policy Engine
4. Deterministic Executor
5. Reasoning Engine
6. Validation Engine
7. Learning & Capability Manager

Supporting concerns include the Capability Registry, observability, security, and governance.

## Canonical flow

```text
Request
  ↓
Normalize
  ↓
Resolve known capability
  ↓
Policy / confidence / risk decision
  ├── safe known path → deterministic execution → validate → result
  └── unknown/unsafe path → reasoning → execute → validate → learn
                                                   ↓
                                           artifact candidate
                                                   ↓
                                               promote
                                                   ↓
                                         Capability Registry
```

## Key terminology

- **Known vs. Unknown** — the fundamental routing boundary.
- **Artifact Promotion** — the process that turns an LLM-generated hypothesis into trusted reusable capability through evidence and controls.
- **Executable Memory** — what the system knows *how to do*, not merely what it knows.
- **Confidence-Gated Reuse** — deterministic reuse only when confidence and risk permit it.
- **Failure-Triggered Relearning** — validation failure returns the task to the Intelligence Plane.
- **Self-Healing Automation** — detected invalidity followed by intelligent repair, validation, and promotion; retry alone is not self-healing.

## Reference repository structure vs. this repository

The chapter presents a conceptual future architecture with shared packages such as `routing/`, `execution/`, `validation/`, `learning/`, `registry/`, `security/`, and `observability/`.

The public companion repository starts **chapter-first** instead. That is deliberate. We do not want to manufacture a framework before the implementations prove which abstractions deserve to be shared.

[Chapter 3](../chapter-03-web-research/) is the first runnable proof of the architecture.
