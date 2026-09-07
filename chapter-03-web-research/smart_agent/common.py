"""Shared source-discovery and prompt helpers."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from .fetcher import FetchedPage, WebFetcher
from .model_provider import ModelProvider
from .models import ModelUsage, SourceSelection, TaskDescriptor, ToolUsage
from .search_provider import SerperSearchProvider

ROOT = Path(__file__).resolve().parents[1]


def load_prompt(name: str) -> str:
    return (ROOT / "prompts" / name).read_text(encoding="utf-8")


def domain_matches(url: str, expected_domain: str) -> bool:
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    expected = expected_domain.lower().removeprefix("www.")
    return host == expected or host.endswith("." + expected)


def resolve_source(task: TaskDescriptor, provider: ModelProvider) -> tuple[str, ModelUsage, ToolUsage]:
    """Use explicit URL when known; otherwise search, filter, then let the model choose."""
    model_usage, tool_usage = ModelUsage(), ToolUsage()
    if task.pricing_url:
        if task.domain not in {"127.0.0.1", "localhost"} and not domain_matches(task.pricing_url, task.domain):
            raise ValueError(f"pricing_url {task.pricing_url!r} does not match official domain {task.domain!r}")
        return task.pricing_url, model_usage, tool_usage

    if not task.search_query:
        raise ValueError("Task must provide pricing_url or search_query")
    results, search_usage = SerperSearchProvider().search(task.search_query)
    tool_usage.add(search_usage)

    # Cheap structured filtering comes before model judgment. There is no prize for
    # paying an embedding/model to rediscover a domain field we already have.
    candidates = [r for r in results if domain_matches(r.link, task.domain)]
    if not candidates:
        raise RuntimeError(f"No search result matched official domain {task.domain}")

    selection, usage = provider.structured(
        instructions=load_prompt("source-selection-v1.txt"),
        input_text=json.dumps({
            "expected_domain": task.domain,
            "results": [r.__dict__ for r in candidates[:8]],
        }, indent=2),
        response_model=SourceSelection,
        schema_name="chapter3_source_selection",
    )
    model_usage.add(usage)
    if not selection.selected_url or not domain_matches(selection.selected_url, task.domain):
        raise RuntimeError("Model did not select a valid official-domain source")
    return selection.selected_url, model_usage, tool_usage


def fetch_for_model(url: str, mode: str = "auto") -> tuple[FetchedPage, ToolUsage]:
    return WebFetcher().fetch(url, mode)
