# Changelog

## v1.1

Real-model hardening after the first OpenAI demo run.

- Added `smart_agent/normalizer.py`, a deterministic semantic normalization layer shared by the Reasoning-First baseline and Smart Agent.
- Canonicalized common billing-period forms such as `per month`, `/mo`, `monthly`, `per year`, and `annually`.
- Canonicalized common currency symbols/codes.
- Added optional `currency` `FieldRule` to `ExtractionRecipe` for pages that render amount and currency separately.
- Updated deterministic extraction to infer currency from complete price text first and fall back to an explicit currency rule.
- Strengthened discovery and repair prompts so learned price rules preserve currency evidence instead of stripping `$`, `USD`, and similar information.
- Normalized direct model output before promotion validation so both architectures are judged through the same trusted semantic contract.
- Kept all artifact-promotion validation gates strict.
- Surfaced Smart Agent promotion failures directly in console output.
- Added regression tests for the exact cases revealed by the first real-model run.
- Clarified that Serper pricing is user-supplied and not used by the controlled benchmark.

## v1.0

Initial Chapter 3 implementation.
