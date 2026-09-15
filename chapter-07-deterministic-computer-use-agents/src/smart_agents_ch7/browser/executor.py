from __future__ import annotations

import os
from pathlib import Path
import time
from typing import Any

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from .models import BrowserExecution, BrowserPlan


def _render_value(value: str | None, args: dict[str, Any], transform: str | None = None) -> str:
    if value is None:
        return ""
    if value.startswith("{{") and value.endswith("}}"):
        key = value[2:-2].strip()
        raw = args.get(key, "")
        if transform == "dollars_to_cents":
            return str(int(round(float(raw) * 100)))
        return str(raw)
    return value


class BrowserExecutor:
    def __init__(self, base_url: str, timeout_ms: int = 5000, headless: bool = True):
        self.base_url = base_url.rstrip("/")
        self.timeout_ms = timeout_ms
        self.headless = headless
        self._pw = None
        self._browser = None
        self._context = None

    def __enter__(self) -> "BrowserExecutor":
        self._pw = sync_playwright().start()
        launch_kwargs: dict[str, Any] = {"headless": self.headless}
        explicit = os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
        if explicit:
            launch_kwargs["executable_path"] = explicit
        elif Path("/usr/bin/chromium").exists():
            launch_kwargs["executable_path"] = "/usr/bin/chromium"
        self._browser = self._pw.chromium.launch(**launch_kwargs)
        self._context = self._browser.new_context()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    def execute(self, plan: BrowserPlan, args: dict[str, Any]) -> BrowserExecution:
        if not self._context:
            raise RuntimeError("BrowserExecutor must be used as a context manager")
        page = self._context.new_page()
        page.set_default_timeout(self.timeout_ms)
        extracted: dict[str, str] = {}
        started = time.perf_counter()
        count = 0
        try:
            for action in plan.actions:
                count += 1
                if action.kind == "goto":
                    path = action.target or plan.start_path
                    page.goto(self.base_url + path, wait_until="domcontentloaded")
                elif action.kind == "fill":
                    value = _render_value(action.value, args)
                    page.locator(action.target or "").fill(value)
                elif action.kind == "select":
                    value = _render_value(action.value, args)
                    page.locator(action.target or "").select_option(value)
                elif action.kind == "check":
                    page.locator(action.target or "").check()
                elif action.kind == "click":
                    page.locator(action.target or "").click()
                    page.wait_for_load_state("domcontentloaded")
                elif action.kind == "extract":
                    key = action.key or "value"
                    extracted[key] = page.locator(action.target or "").inner_text().strip()
                else:
                    raise ValueError(f"Unsupported action kind: {action.kind}")
            elapsed = (time.perf_counter() - started) * 1000
            return BrowserExecution(True, extracted, count, elapsed_ms=elapsed)
        except Exception as exc:
            elapsed = (time.perf_counter() - started) * 1000
            return BrowserExecution(False, extracted, count, error=f"{type(exc).__name__}: {exc}", elapsed_ms=elapsed)
        finally:
            page.close()
