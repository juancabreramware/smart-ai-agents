# Chapter 8 — Understand the Document Once
## Building Self-Learning Document Pipelines

Evidence-first companion implementation for *Smart AI Agents — Don't Let Tokens Eat Up Your Budget*.

Three architectures process the same frozen synthetic HarborPoint corpus:

- **Baseline** — LLM extraction on every document.
- **Smart** — learn a validated Executable Document Capability, deterministically reuse it while compatibility gates pass, selectively invalidate/relearn on drift, and preserve an explicit semantic-reasoning path.
- **Naive** — coarse family reuse without Smart compatibility/invalidation protections.

Canonical benchmark: 150 documents per architecture, phases A/B/C, six families, controlled V1→V2 drift, 18 reasoning-required requests. Canonical PDFs are text-native to isolate document understanding/reuse from OCR quality.

## Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,openai]"
pytest
```

## Generate and validate the frozen candidate corpus
```powershell
python scripts/generate_corpus.py
python scripts/run_demo.py --planner mock --output evidence\demo-mock-v1
python scripts/run_benchmark.py --planner mock --output evidenceull-mock-v1
python scripts/audit_evidence.py evidenceull-mock-v1
```

After the mock evidence is audited, run the real ~15-document demo before any canonical real-model benchmark:
```powershell
$env:OPENAI_API_KEY="..."
python scripts/run_demo.py --planner openai --output evidence\demo-real-v1
```

Do **not** run the canonical real-model benchmark until the corpus, workload, contracts, code, model settings, pricing manifest, and audit path are frozen.

## Real benchmark (only after the decision gate)
```powershell
python scripts/run_benchmark.py --planner openai --output evidenceull-real-v1
python scripts/audit_evidence.py evidenceull-real-v1
python scripts/freeze_evidence.py evidenceull-real-v1 --name chapter-08-full-real-v1.0-evidence.zip
```

Raw JSONL ledgers are authoritative. Summary files are derived convenience artifacts only.
