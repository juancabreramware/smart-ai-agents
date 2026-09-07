"""Execution ledger, manifest, and reproducibility helpers."""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

from .models import ExperimentManifest, ExecutionLedgerEntry
from .settings import settings


def new_execution_id() -> str:
    return f"exec_{uuid4().hex[:16]}"


class LedgerWriter:
    def __init__(self, experiment_id: str) -> None:
        self.experiment_id = experiment_id
        self.dir = settings.ledger_dir / experiment_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / "executions.jsonl"

    def append(self, entry: ExecutionLedgerEntry) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")

    def reset(self) -> None:
        if self.path.exists():
            self.path.unlink()


def current_git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=settings.root,
            stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        return None


def write_manifest(experiment_id: str, provider_name: str, model_name: str, config: dict) -> Path:
    directory = settings.ledger_dir / experiment_id
    directory.mkdir(parents=True, exist_ok=True)
    manifest = ExperimentManifest(
        experiment_id=experiment_id,
        provider=provider_name,
        model_name=model_name,
        git_commit=current_git_commit(),
        python_version=sys.version,
        platform=platform.platform(),
        config=config,
        pricing_snapshot={
            "openai_input_usd_per_million": settings.openai_input_usd_per_million,
            "openai_cached_input_usd_per_million": settings.openai_cached_input_usd_per_million,
            "openai_output_usd_per_million": settings.openai_output_usd_per_million,
            "serper_usd_per_1000_searches": settings.serper_usd_per_1000_searches,
        },
    )
    path = directory / "manifest.json"
    path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return path
