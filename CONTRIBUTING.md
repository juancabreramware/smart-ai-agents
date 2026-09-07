# Contributing

This repository is primarily the executable companion to *Smart AI Agents — Don't Let Tokens Eat Up Your Budget*.

Bug reports, reproducibility reports, and focused improvements are welcome. For implementation changes:

1. Keep the chapter's experimental contract intact.
2. Do not weaken validation merely to make a benchmark pass.
3. Add or update tests for behavior changes.
4. Do not commit secrets, local `.env` files, generated benchmark output, or learned runtime capability files.
5. Clearly distinguish measured results from projections or hypothetical economics.

Before opening a pull request for Chapter 3, run:

```bash
cd chapter-03-web-research
python -m pip install -r requirements.txt
pytest -q
```
