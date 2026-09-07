"""Optional Serper search provider used by live source discovery."""

from __future__ import annotations

from dataclasses import dataclass
import requests

from .models import ToolUsage
from .settings import settings


@dataclass
class SearchResult:
    title: str
    link: str
    snippet: str = ""


class SerperSearchProvider:
    def __init__(self) -> None:
        if not settings.serper_api_key:
            raise RuntimeError("SERPER_API_KEY is required when pricing_url is omitted")

    def search(self, query: str, num: int = 10) -> tuple[list[SearchResult], ToolUsage]:
        response = requests.post(
            settings.serper_endpoint,
            headers={"X-API-KEY": settings.serper_api_key, "Content-Type": "application/json"},
            json={"q": query, "num": num},
            timeout=settings.http_timeout_seconds,
        )
        if not response.ok:
            raise RuntimeError(f"Serper returned HTTP {response.status_code}: {response.text[:1000]}")
        results = [
            SearchResult(title=x.get("title", ""), link=x.get("link", ""), snippet=x.get("snippet", ""))
            for x in (response.json().get("organic") or []) if x.get("link")
        ]
        return results, ToolUsage(search_calls=1, cost_usd=settings.serper_usd_per_1000_searches / 1000.0)
