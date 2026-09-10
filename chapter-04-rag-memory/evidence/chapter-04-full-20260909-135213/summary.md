# Chapter 4 Benchmark Summary

Mode: full
Provider: openai
Embeddings: openai

## baseline
- Correctness: 0.940
- LLM calls: 150
- Memory reuse rate: 0.0%
- LLM avoidance: 0.0%
- Incorrect stale reuse: 0
- Total measured configured cost: $0.207336

## smart
- Correctness: 1.000
- LLM calls: 41
- Memory reuse rate: 72.7%
- LLM avoidance: 72.7%
- Incorrect stale reuse: 0
- Total measured configured cost: $0.067540

## naive_cache
- Correctness: 0.727
- LLM calls: 35
- Memory reuse rate: 0.0%
- LLM avoidance: 76.7%
- Incorrect stale reuse: 37
- Total measured configured cost: $0.059035
