# Chapter 5 Experimental Specification v1.0 — Implementation Snapshot

Scenario: fictional Northstar Manufacturing Group corporate IT onboarding/offboarding.
Primary hypothesis: validated, versioned workflow capabilities can replace repeated LLM planning while preserving correctness.
Architectures: Baseline Planning Agent, Smart Workflow Agent, Naive Plan Cache ablation.
Workload: exactly 150 requests per architecture; V1 first 100, V2 final 50.
V2 deliberate changes: Engineering MFA before repository access; Finance security-awareness before access.
Selective invalidation required: unchanged workflow capabilities must survive.
Headline economics and savings are not predefined and must come only from the real benchmark.
