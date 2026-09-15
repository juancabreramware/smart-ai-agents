# Chapter 7 Companion Implementation — Local Validation

Status: **PASS for implementation/local architecture validation**

This report is not publication evidence and must not be used for Chapter 7 benchmark claims.

## Test suite

- 12 tests collected
- 11 passed
- 1 skipped
- The skipped test is the opt-in real Playwright localhost integration test. The current build environment blocks Chromium localhost navigation by administrator policy; enable it on a normal development machine with `CH7_RUN_PLAYWRIGHT_TESTS=1`.

## 15-request mock/simulated demo

- Baseline: 15/15 correct, 15 planner calls
- Smart: 15/15 correct, 10 planner calls, 5 deterministic reuses, 4 V2 relearning events, 0 stale reuses
- Naive: 11/15 correct, 6 planner calls, 4 stale V2 failures
- Independent raw-ledger audit: PASS

## 150-request mock/simulated validation

- Baseline: 150/150 correct, 150 planner calls
- Smart: 150/150 correct, 28 planner calls
  - 6 initial acquisitions
  - 18 reasoning-required executions
  - 4 relearning events
  - 122 deterministic reuses
  - 0 stale reuses
- Naive: 118/150 correct, 24 planner calls, 32 stale/incorrect V2 reuses
- Independent raw-ledger audit: PASS

Again, these values validate architecture/control flow only. They are deliberately excluded from publication claims because the planner is mock and the executor is simulated.

## Frozen candidate workload fingerprints

`workloads/benchmark_v1.0.jsonl`

`74e03f916c6d768e0404ffcc5f1440035b5d431c4f33faa46f4873f909ed4737`

`workloads/demo_v1.0.jsonl`

`6306320c9217a393b9468440986e571b716e1e0ffb39d0402b997c87edde8533`

## Next gate

Run the real 15-request demo using GPT-5.6 Sol + Playwright. Do not execute the real 150-request benchmark until the demo is audited and any real-model normalization issues have regression tests.
