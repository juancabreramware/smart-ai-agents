# v1.2
- Added deterministic schema-aware answer canonicalization for real-model representational noise.
- Ignores terminal sentence periods and case/whitespace differences in structured string values.
- Treats a redundant trailing `support` token as equivalent inside the `support` field only.
- Baseline, Smart, and Naive Cache now share the same deterministic correctness function.
- Naive stale-reuse classification now uses the same correctness semantics.
- Added regression tests for the GPT-5.6 d007/d015 variants while preserving structural strictness.

# Changelog

## v1.1
- Hardened the real OpenAI provider with intent-specific strict structured-output schemas.
- Canonical answers now use the same deterministic representation as the locked workload instead of allowing model-selected field names.
- Retained exact deterministic validation; no fuzzy or semantic correctness relaxation was introduced.
- Added regression coverage for canonical simple/compositional/reasoning-required schemas.
- Added unchanged-fact V1→V2 naive-cache regression coverage so unchanged reuse is not mislabeled stale.

## v1.0
- Initial implementation from Chapter 4 Experimental Specification v1.0.
- Baseline RAG, Smart Agent, and naive semantic-cache ablation.
- Versioned Northstar Cloud V1/V2 corpus and deterministic ground truth.
- Fixed 15-query demo and 150-query full workload.
- Provenance-backed memory, selective invalidation, reasoning policy, telemetry, economics, and tests.
