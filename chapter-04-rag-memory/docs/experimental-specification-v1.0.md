# Smart AI Agents - Chapter 4 Experimental Specification v1.0

**Status:** LOCKED FOR IMPLEMENTATION

**Version:** 1.0

**Book:** *Smart AI Agents - Don't Let Tokens Eat Up Your Budget*


## 1. Purpose and Experimental Thesis

Chapter 4 tests whether a Smart Agent can reuse validated knowledge without invoking an LLM on every request, while preserving correctness when the source knowledge changes, confidence is insufficient, or the request genuinely requires new reasoning.

Chapter title:
Don't Ask the LLM What You Already Know
RAG, Memory, and Intelligent Reuse

Primary hypothesis:
A Smart Agent can answer recurring knowledge questions from validated, provenance-backed memory without invoking an LLM on every request, while preserving correctness by invalidating or bypassing memory when source knowledge changes, confidence is insufficient, or the question requires new reasoning.

Secondary hypothesis:
Simple semantic caching is not sufficient. Safe reuse requires provenance, source-version awareness, validation, confidence gating, and explicit fallback to reasoning.

The experiment is intended to test the architecture, not to force a favorable result. If memory lookup, validation, embeddings, or invalidation overhead make the Smart Agent less economical for a low-repetition workload, that result must be reported.


## 2. What Chapter 4 Must Prove

Chapter 3 demonstrated capability reuse: the agent learned how to perform a recurring web-research task, preserved that capability, executed it deterministically, detected a structural change, and relearned.

Chapter 4 focuses on semantic knowledge reuse: the agent should know when it already possesses a validated answer and when it must return to source evidence and reasoning.

The experiment must establish all of the following:
- Repeated safe factual questions can bypass the LLM after knowledge acquisition.
- The Smart Agent can recognize paraphrases of a previously learned intent.
- Reused knowledge remains tied to provenance and source versions.
- Changes to source knowledge invalidate only affected memories, not the entire memory store.
- Stale knowledge is detected before it is returned.
- Novel, ambiguous, or policy-sensitive questions still invoke reasoning.
- A naive semantic cache can fail even when semantic similarity is high.
- Correctness is measured against deterministic ground truth rather than an LLM judge wherever possible.
- The economic result is measured honestly, including memory, embedding, retrieval, validation, and relearning costs.


## 3. Controlled Domain: Northstar Cloud Knowledge Base

The controlled domain is a fictional SaaS provider named Northstar Cloud. Reusing the fictional company from Chapter 3 gives continuity while changing the problem class from procedural learning to knowledge reuse.

The controlled knowledge base contains versioned Markdown documents:
- pricing.md
- billing.md
- cancellations.md
- data-retention.md
- security.md
- api-limits.md
- support.md
- integrations.md
- regions.md

Each document must contain stable identifiers for factual statements so that the benchmark can track provenance at fact-level granularity. The corpus must be small enough to inspect manually but rich enough to create factual, compositional, ambiguous, and reasoning-required questions.

Each knowledge-base version also has a machine-readable ground-truth file containing the canonical facts used by the benchmark.


## 4. Knowledge Base V1 - Locked Facts

The following facts define V1 and must be treated as canonical ground truth:

Pricing and billing:
- Starter plan: $29 per month.
- Professional plan: $99 per month.
- Enterprise plan: custom pricing.
- Annual billing discount: 15%.
- Refund policy: no prorated refunds after a billing period begins.

API limits:
- Starter: 1,000 requests per hour.
- Professional: 10,000 requests per hour.
- Enterprise: 100,000 requests per hour by default, with custom limits available.

Data retention:
- Production application logs: 14 days.
- Backups: 30 days.
- Deleted-account data: 7 days after account closure before permanent deletion.
- Audit logs on Enterprise: 365 days.

Support:
- Starter: business-day email support.
- Professional: 24/5 support.
- Enterprise: 24/7 support.

Regions:
- United States primary region: Virginia.
- European Union region: Frankfurt.
- Asia-Pacific region: Singapore.

Security:
- Data encrypted at rest with AES-256.
- Data encrypted in transit with TLS 1.3 where supported.
- SSO/SAML available on Enterprise.
- SOC 2 Type II report available to qualified customers under NDA.

Cancellations:
- Cancellation takes effect at the end of the current paid billing period.
- Access remains active until the end of the billing period.

Integrations:
- Native Slack integration available on Professional and Enterprise.
- Salesforce integration available on Enterprise.
- Webhooks available on all paid plans.


## 5. Knowledge Base V2 - Deliberate World Change

After the first 100 executions, the benchmark changes the corpus from V1 to V2. V2 must contain a mixture of changed and unchanged facts so invalidation can be selective.

Required V2 changes:
- Backup retention changes from 30 days to 45 days.
- Starter API limit changes from 1,000/hour to 2,500/hour.
- Enterprise support changes from unconditional 24/7 support to: P1 incidents 24/7; standard tickets business hours.
- EU regions change from Frankfurt only to Frankfurt and Dublin.
- Annual billing discount changes from 15% to 20%.

Required unchanged facts:
- Starter price remains $29/month.
- Professional price remains $99/month.
- Production application logs remain 14 days.
- Enterprise audit logs remain 365 days.
- Slack integration remains Professional and Enterprise.
- Cancellation still takes effect at the end of the current paid billing period.
- AES-256 at rest remains unchanged.
- SSO/SAML remains Enterprise-only.

The experiment must prove that memories supported only by unchanged source facts remain reusable while memories depending on changed facts are invalidated before return.


## 6. Compared Architectures

A. Baseline RAG Agent
Every request performs retrieval and then invokes the LLM with retrieved evidence. There is no cross-request reusable answer memory.

Canonical path:
Question -> normalize -> retrieve top-k evidence -> LLM -> structured answer -> validate -> return

The baseline must be competent and fair. It may use the same retriever, same model, same chunking, and same output schema as the Smart Agent. It simply does not reuse previously validated answers across requests.

B. Smart Agent
The Smart Agent adds validated semantic memory before the Reasoning Path.

Canonical path:
Question -> normalize -> memory resolver
- If no candidate memory: retrieve evidence -> LLM -> validate -> promote memory -> return
- If candidate memory exists: validate intent match, confidence, provenance, source version, and reuse policy
  - If safe: deterministic answer from memory
  - If unsafe/invalid: retrieve evidence -> LLM -> validate -> replace/promote memory -> return

C. Naive Semantic Cache Ablation
This is a safety demonstration, not the primary economic comparator.

Canonical path:
Question embedding -> nearest cached question
- If similarity exceeds threshold: reuse cached answer
- Otherwise: baseline RAG + LLM and cache result

The naive cache deliberately lacks provenance validation and source-version awareness. It should demonstrate why semantic similarity alone is not sufficient for safe knowledge reuse.


## 7. Memory Object Schema

A reusable memory record must store more than an answer string. Minimum schema:

{
  "memory_id": "backup-retention",
  "canonical_intent": "backup_retention_period",
  "query_family": "reusable_fact",
  "answer": {"days": 30},
  "source_refs": [
    {
      "document": "data-retention.md",
      "fact_id": "retention.backups",
      "source_version": "v1",
      "content_hash": "..."
    }
  ],
  "confidence": 0.99,
  "validation_status": "validated",
  "created_at": "...",
  "last_validated_at": "...",
  "reuse_count": 0,
  "expires_at": null
}

Required properties:
- canonical intent
- structured answer
- source provenance
- source version and/or content hash
- confidence
- validation status
- timestamps
- reuse count
- optional expiration

The experiment must not treat an embedding similarity score as proof of validity.


## 8. Query Classes

The full workload contains four query classes.

Class A - Reusable factual knowledge
Examples:
- How long are backups retained?
- What's the backup retention period?
- For how many days does Northstar keep backups?

Expected behavior:
After acquisition, safe paraphrases should reuse validated memory without an LLM call.

Class B - Reusable normalized facts
Examples:
- What is the Starter API rate limit?
- How many API calls per hour does Starter allow?
- Starter request limit?

Expected behavior:
The normalizer maps wording differences to the same canonical intent and structured unit.

Class C - Compositional questions
Examples:
- Does Enterprise provide 24/7 support in the EU?
- Can a Professional customer use Slack and receive 24/5 support?

Expected behavior:
If all required atomic facts are validated and the composition rule is deterministic, reuse may be permitted. Otherwise the request must fall back to reasoning.

Class D - Ambiguous or reasoning-required questions
Examples:
- Is Northstar suitable for a heavily regulated financial company?
- Is the Professional plan a better fit than Enterprise for our company?
- Does Northstar meet all of my organization's compliance obligations?

Expected behavior:
The Smart Agent must not answer solely from memory merely because related facts are available. These questions require interpretation, missing context, or risk-sensitive judgment and should invoke the LLM.


## 9. Full Workload - 150 Executions

The benchmark uses exactly 150 fixed requests per architecture.

Phase 1 - V1 knowledge base: 100 executions
- 72 reusable factual/normalized requests across 16 canonical intents.
- 16 compositional requests across 2 canonical compositions.
- 12 reasoning-required or ambiguous requests across 2 canonical intents.

Phase 2 - V2 knowledge base: 50 executions
- 30 requests that target changed facts.
- 10 requests that target unchanged facts.
- 5 compositional requests spanning at least one changed fact.
- 5 reasoning-required or ambiguous requests.

The workload must be committed to the repository as deterministic JSON. Queries are not generated at benchmark runtime.

Each request record must include:
- query_id
- phase
- source_version
- class
- canonical_intent
- query text
- expected structured answer or expected decision category
- expected sources
- whether deterministic memory reuse is allowed
- whether an LLM call is required by policy


## 10. Canonical Intent Set

The initial 20 canonical intents are locked as follows.

Reusable facts / normalized facts:
1. starter_price_monthly
2. professional_price_monthly
3. annual_discount_percentage
4. starter_api_limit_hourly
5. professional_api_limit_hourly
6. backup_retention_days
7. application_log_retention_days
8. deleted_account_retention_days
9. enterprise_audit_log_retention_days
10. starter_support_level
11. professional_support_level
12. enterprise_support_level
13. eu_regions
14. cancellation_effective_time
15. slack_integration_plans
16. sso_saml_plan

Compositional:
17. enterprise_support_in_eu
18. professional_slack_and_support

Reasoning-required:
19. regulated_financial_company_suitability
20. plan_recommendation_for_company

The exact paraphrases are fixed in workload files and reviewed before the benchmark is run.


## 11. Demo Workload - 15 Executions

A fast demo mode must make the architecture visible to readers without requiring the full benchmark.

Demo sequence:
V1 - 10 requests
- First query for backup retention -> REASONING / ACQUIRE
- Two paraphrases of backup retention -> MEMORY
- First query for Starter API limit -> REASONING / ACQUIRE
- One paraphrase -> MEMORY
- First Enterprise support query -> REASONING / ACQUIRE
- One compositional query
- One ambiguous query -> REASONING_REQUIRED
- Two additional safe reuse queries

Switch V1 -> V2

V2 - 5 requests
- Backup retention query -> SOURCE_CHANGED / INVALIDATE / REASON / PROMOTE V2
- Backup paraphrase -> MEMORY V2
- Starter API limit query -> SOURCE_CHANGED / INVALIDATE / REASON / PROMOTE V2
- Unchanged Starter price query -> MEMORY remains valid
- Enterprise support compositional query -> invalidation and appropriate fallback

Console output should make path decisions explicit.


## 12. Validation Policy

Every memory reuse decision must pass the following gates.

1. Technical validation
The memory record is readable, structurally valid, and compatible with the current schema.

2. Intent validation
The normalized query matches the memory's canonical intent above the configured confidence threshold.

3. Provenance validation
The memory contains source references to the facts that justify the answer.

4. Source-version validation
Every referenced fact still maps to the same source version/content hash. A mismatch invalidates the affected memory.

5. Evidence validation
The current source still supports the structured answer represented in memory.

6. Reuse-policy validation
The query class is permitted to bypass reasoning. Ambiguous, recommendation, compliance, or other risk-sensitive classes may require reasoning even when related facts are known.

7. Output validation
The returned structured answer must satisfy the canonical output schema and ground-truth constraints.

A failed validation gate must not silently degrade into stale reuse.


## 13. Source Change and Selective Invalidation Protocol

When V2 is activated, the system must detect changes at source-fact granularity where feasible.

Required behavior:
- Compute stable identifiers and content hashes for source facts/chunks.
- Mark only memory records that depend on changed facts as invalid.
- Preserve memory records whose supporting facts are unchanged.
- On the next query that hits an invalidated memory, route to evidence retrieval and reasoning.
- Validate the new answer against V2 ground truth.
- Promote a new memory version with V2 provenance.
- Subsequent safe paraphrases reuse the new memory without LLM inference.

A global "clear all memory" operation does not satisfy the selective-invalidation requirement.


## 14. Ground Truth and Correctness Scoring

Ground truth must be deterministic whenever possible.

For factual and normalized queries:
- Exact structured-value comparison after normalization.
- Numeric values compare in canonical units.
- Enumerations compare as normalized sets.
- Boolean/availability fields compare exactly.

For compositional questions:
- Expected answer is computed from ground-truth atomic facts using deterministic composition rules where possible.

For reasoning-required questions:
- The primary correctness criterion is policy behavior: the Smart Agent must route to reasoning rather than falsely claiming deterministic reuse.
- If a final textual answer is evaluated, the benchmark must separate routing correctness from answer quality and clearly label any model-based evaluation.

Primary correctness metric:
successful_ground_truth_matches / scored_requests

The benchmark must report factual correctness separately from routing-policy correctness.


## 15. Metrics - Required Instrumentation

Execution metrics:
- executions
- successful executions
- failed executions
- correctness rate
- routing-policy correctness

LLM metrics:
- LLM calls
- input tokens
- cached input tokens
- output tokens
- model cost

Retrieval/memory metrics:
- embedding calls
- vector retrievals
- document retrievals
- memory lookups
- memory hits
- memory misses
- memory invalidations
- memory promotions
- memory replacements
- fallbacks
- acquisition calls
- relearning calls

Safety/freshness metrics:
- stale-memory opportunities
- stale-memory detections
- stale-memory detection rate
- incorrect stale reuse
- false invalidations
- unchanged-memory reuse after V2

Latency:
- mean latency
- median latency
- P95 latency

Economics:
- embedding cost
- retrieval cost
- memory-store cost if measurable
- validation cost
- model cost
- total measured cost
- acquisition cost
- relearning cost
- cumulative savings
- break-even execution count

Efficiency:
- memory reuse rate
- fallback rate
- LLM avoidance rate


## 16. Economic Model

Baseline:
C_baseline = N x (C_retrieval + C_LLM + C_validation)

Smart:
C_smart = C_acquisition + C_memory_lookup + C_memory_validation + C_residual_retrieval + C_residual_LLM + C_relearning + C_maintenance

The experiment must not count "avoided model cost" while ignoring additional Smart Agent costs.

Required reported economics:
- total measured cost for each architecture
- cost per execution
- cost per correct execution
- first-acquisition cost
- relearning cost after V2
- memory/embedding/retrieval overhead
- cumulative savings or loss
- break-even execution count if a break-even exists

Measured economics and projected economics must be clearly separated.


## 17. Acceptance Criteria

The implementation passes Chapter 4 experimental validation only if all of the following are true:

Correctness
- Baseline and Smart Agent complete the benchmark successfully enough to support comparison.
- Smart factual correctness is not lower than baseline factual correctness without explicit explanation.

Freshness
- Every V2 changed-fact memory opportunity is detected before stale output is returned.
- Target: incorrect_stale_reuse = 0.

Selective reuse
- Safe recurring factual requests bypass the LLM after acquisition.

Selective invalidation
- Unchanged memories remain reusable after V2.
- The implementation must not rely on clearing the entire memory store.

Selective reasoning
- Ambiguous, recommendation, compliance, or other policy-sensitive questions continue to invoke reasoning when required.

Recovery
- Changed knowledge follows: detect change -> invalidate -> retrieve -> reason -> validate -> promote replacement -> reuse.

Reproducibility
- A fresh clone can run tests, demo, and full benchmark from documented commands.

Economic honesty
- The result is reported whether Smart wins, loses, or breaks even.


## 18. Failure Conditions

The experiment is considered failed or inconclusive if any of the following occur:
- The Smart Agent returns a stale V1 fact after the corresponding V2 source has changed.
- The system clears all memory at V2 instead of performing selective invalidation.
- The baseline is intentionally weakened in a way the Smart Agent does not share.
- Runtime query generation makes exact reproduction impossible.
- Ground truth is judged primarily by an LLM when deterministic comparison is available.
- Token or cost accounting excludes material Smart Agent overhead.
- A semantic-similarity threshold is treated as sufficient evidence of correctness.
- The Smart Agent routes policy-sensitive questions to deterministic reuse simply because related facts are known.
- Results are manually edited rather than emitted from the benchmark pipeline.


## 19. Reproducibility and Repository Contract

Target repository folder:

chapter-04-rag-memory/
  README.md
  .env.example
  requirements.txt
  baseline/
  smart_agent/
  naive_cache/
  knowledge_base/
    v1/
    v2/
    ground_truth/
  workloads/
    demo.json
    full.json
  experiments/
    run.py
    metrics.py
    economics.py
  results/
  tests/

Required commands:

python -m experiments.run --mode demo
python -m experiments.run --mode full
pytest -q

The repository must not include API keys, local .env files, generated caches, temporary run folders, or nonessential trial-run debris. Benchmark result artifacts intended to support the book may be committed separately after the run is complete and verified.


## 20. Model and Provider Controls

For the primary comparison:
- Use the same LLM model for Baseline and Smart Agent reasoning calls.
- Use the same embedding model for equivalent retrieval tasks.
- Use the same source corpus, chunking, retrieval parameters, and output schema unless a difference is itself part of the architecture being tested.
- Record exact model identifiers and pricing assumptions at run time.
- Pin benchmark configuration in a machine-readable manifest.

Model choice must be configurable through environment variables. No benchmark claim should depend on an undocumented provider default.


## 21. Result Artifacts

The full benchmark must emit:
- run_manifest.json
- execution_ledger.jsonl
- summary.json
- summary.md
- economics.json
- routing_breakdown.json
- memory_events.jsonl
- stale_memory_report.json
- latency_summary.json
- token_cost_summary.json
- benchmark_results.csv

Optional publication charts may be generated from these artifacts, but the underlying machine-readable results are authoritative.


## 22. Planned Chapter 4 Narrative Evidence

The implementation and benchmark should provide evidence for the following chapter arguments, but none may be stated as measured fact until the run supports it:

- RAG retrieves knowledge; memory preserves validated knowledge.
- Retrieval before reasoning can reduce unnecessary inference.
- Similarity is not validity.
- Provenance is part of memory, not metadata decoration.
- Source change should invalidate dependent memory, not all memory.
- Memory is useful only when the system knows when not to trust it.
- The objective is not maximum cache hit rate; it is maximum safe reuse.
- Some questions remain reasoning problems even when all relevant facts are available.
- The economics of semantic memory depend on repetition, retrieval cost, validation cost, change frequency, and the cost of being wrong.


## 23. Locked Signature Lines

The following phrases are approved as conceptual anchors for Chapter 4:

"Don't ask the LLM what you already know."

"Retrieve Before Reasoning."

"Similarity is not validity."

"RAG retrieves knowledge. Memory preserves validated knowledge. Policy decides when knowledge is trustworthy enough to replace reasoning."

"The objective is not maximum cache hit rate. The objective is maximum safe reuse."

"Memory is only intelligent if the system knows when not to trust it."

These are conceptual statements, not benchmark-result claims.


## 24. Specification Freeze

Status: LOCKED FOR IMPLEMENTATION - v1.0

Changes after implementation begins should require a version bump when they materially alter:
- the hypotheses,
- V1/V2 ground truth,
- query-class definitions,
- the 150-execution benchmark shape,
- acceptance criteria,
- correctness scoring,
- or economic accounting.

Minor implementation clarifications that do not alter the experimental claim may be documented without changing the benchmark thesis.

The next step after this specification is to build the complete Chapter 4 implementation and test suite before writing the chapter manuscript.
