"""Fresh page retrieval with requests-first and optional Playwright rendering."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .models import ToolUsage
from .settings import settings


@dataclass
class FetchedPage:
    url: str
    html: str
    visible_text: str
    fetch_mode: str


def simplify_html(html: str, max_chars: int = 60_000) -> tuple[str, str]:
    """Strip noisy tags before model input while preserving DOM hooks/selectors."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "svg", "noscript", "template"]):
        tag.decompose()
    simplified = str(soup)[:max_chars]
    text = soup.get_text("\n", strip=True)[:20_000]
    return simplified, text


class WebFetcher:
    @staticmethod
    def _validate_url(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError(f"Only absolute http/https URLs are allowed: {url}")

    def fetch(self, url: str, mode: str = "auto") -> tuple[FetchedPage, ToolUsage]:
        self._validate_url(url)

        if mode in {"requests", "auto"}:
            try:
                r = requests.get(
                    url,
                    headers={"User-Agent": settings.http_user_agent},
                    timeout=settings.http_timeout_seconds,
                    allow_redirects=True,
                )
                r.raise_for_status()
                html, text = simplify_html(r.text)
                # A tiny body is often a JS shell. In auto mode, fall through to
                # Playwright; in requests mode, honor the capability contract.
                local_host = (urlparse(r.url).hostname or "") in {"127.0.0.1", "localhost"}
                if mode == "requests" or local_host or len(text) >= 200:
                    return FetchedPage(r.url, html, text, "requests"), ToolUsage(http_calls=1)
            except requests.RequestException:
                if mode == "requests":
                    raise

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright rendering was needed. Install requirements and run: "
                "python -m playwright install chromium"
            ) from exc

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=settings.http_user_agent)
            page.goto(url, wait_until="networkidle", timeout=int(settings.playwright_timeout_ms))
            raw = page.content()
            final_url = page.url
            browser.close()
        html, text = simplify_html(raw)
        return FetchedPage(final_url, html, text, "playwright"), ToolUsage(browser_calls=1)
