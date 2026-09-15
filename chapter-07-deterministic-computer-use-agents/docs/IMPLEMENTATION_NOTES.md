# Chapter 7 Implementation Notes

## Control-flow objective

The important branch is not “Can the model operate the browser?” It is:

```text
Do we already possess a validated executable UI capability for this request under the active UI contract?
```

If yes, execute it deterministically and audit the resulting business state.
If no, reason, validate the generated plan, execute it, audit it, and promote it only when it is safe and reusable.

## Smart routing paths

The implementation records four Smart paths:

- `INITIAL_ACQUISITION`
- `DETERMINISTIC_REUSE`
- `REASONING_REQUIRED`
- `RELEARNING`

The raw ledger records each path explicitly so the final chapter can explain **why** each model call occurred rather than reporting only a cache-hit percentage.

## Selective V2 invalidation

The UI contract fingerprint is per operation family, not global. This is deliberate. A global `portal_version=V2` comparison would invalidate the entire registry even though Orders and Customer Contact did not change. That would fail the Chapter 7 selective-invalidation requirement.

## Naive architecture

Naive honors explicitly reasoning-required requests so that its primary defect is isolated: it reuses stored UI procedures without validating active UI-contract compatibility. It does not get Smart's version/fingerprint/route checks or relearning lifecycle.

## Real-model boundary

The real planner receives the business request plus the active structured UI contract and returns a strict structured plan. Request-specific values must remain parameter placeholders such as `{{order_id}}`; promotion stores procedure, not one customer's data.

The real benchmark should not weaken validation if GPT-5.6 produces semantically equivalent but structurally different plan output. If normalization is required, add narrow deterministic canonicalization plus regression tests, preserving the frozen ground truth and acceptance rules.
