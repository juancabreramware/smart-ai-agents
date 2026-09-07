"""Model provider abstraction and OpenAI Responses API implementation.

The real provider uses raw HTTPS rather than teaching an SDK helper that may be renamed
next month. The API call uses JSON Schema Structured Outputs so malformed free-form JSON
does not become the experiment's most exciting feature.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Type, TypeVar

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel

from .models import (
    ExtractionRecipe,
    FieldRule,
    LearnedCapabilityCandidate,
    ModelUsage,
    PricePlan,
    PricingResult,
    SourceSelection,
    utc_now_iso,
)
from .settings import settings

T = TypeVar("T", bound=BaseModel)


def _strict_json_schema(node):
    """Normalize Pydantic JSON Schema to the strict Structured Outputs subset.

    OpenAI strict schemas require object properties to be explicitly closed and all
    declared properties to be listed as required. Nullable fields remain nullable via
    their anyOf/null type; "required" means the key is present, not that its value is
    non-null. Pydantic defaults are a validation concern in Python and are removed from
    the wire schema.
    """
    if isinstance(node, dict):
        node = {k: _strict_json_schema(v) for k, v in node.items() if k != "default"}
        if node.get("type") == "object" or "properties" in node:
            properties = node.get("properties", {})
            node["additionalProperties"] = False
            node["required"] = list(properties.keys())
        return node
    if isinstance(node, list):
        return [_strict_json_schema(v) for v in node]
    return node


class ModelProvider(ABC):
    name: str
    model_name: str

    @abstractmethod
    def structured(self, *, instructions: str, input_text: str, response_model: Type[T], schema_name: str) -> tuple[T, ModelUsage]:
        raise NotImplementedError


def _extract_output_text(payload: dict) -> str:
    """Read output_text content from the raw Responses API response body."""
    pieces: list[str] = []
    for item in payload.get("output", []) or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content", []) or []:
            if content.get("type") == "output_text" and content.get("text"):
                pieces.append(content["text"])
    if not pieces:
        raise RuntimeError(
            "Responses API returned no output_text. "
            f"status={payload.get('status')!r}, error={payload.get('error')!r}"
        )
    return "\n".join(pieces)


class OpenAIResponsesProvider(ModelProvider):
    name = "openai"

    def __init__(self) -> None:
        settings.validate_openai()
        self.model_name = settings.openai_model

    @staticmethod
    def _cost(input_tokens: int, cached: int, output_tokens: int) -> float:
        # Cached tokens are a subset of input tokens, so remove them from the normal
        # input bucket before applying the separate cached-input rate.
        uncached = max(0, input_tokens - cached)
        return (
            uncached / 1_000_000 * settings.openai_input_usd_per_million
            + cached / 1_000_000 * settings.openai_cached_input_usd_per_million
            + output_tokens / 1_000_000 * settings.openai_output_usd_per_million
        )

    def structured(self, *, instructions: str, input_text: str, response_model: Type[T], schema_name: str) -> tuple[T, ModelUsage]:
        schema = _strict_json_schema(response_model.model_json_schema())
        body = {
            "model": self.model_name,
            "instructions": instructions,
            "input": input_text,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                }
            },
            "store": False,
        }
        response = requests.post(
            settings.openai_responses_endpoint,
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=max(60.0, settings.http_timeout_seconds),
        )
        if not response.ok:
            raise RuntimeError(
                f"OpenAI Responses API returned HTTP {response.status_code}: {response.text[:2000]}"
            )
        raw = response.json()
        parsed = response_model.model_validate_json(_extract_output_text(raw))
        usage_raw = raw.get("usage") or {}
        input_tokens = int(usage_raw.get("input_tokens") or 0)
        output_tokens = int(usage_raw.get("output_tokens") or 0)
        details = usage_raw.get("input_tokens_details") or {}
        cached = int(details.get("cached_tokens") or 0)
        usage = ModelUsage(
            calls=1,
            input_tokens=input_tokens,
            cached_input_tokens=cached,
            output_tokens=output_tokens,
            cost_usd=self._cost(input_tokens, cached, output_tokens),
            response_ids=[raw.get("id", "")],
        )
        return parsed, usage


class MockModelProvider(ModelProvider):
    """Zero-cost plumbing test for the controlled site.

    Do not use mock numbers in the book. This class only proves the orchestration before
    readers spend money. It recognizes the known fixture shapes deterministically.
    """
    name = "mock"
    model_name = "deterministic-mock"

    def structured(self, *, instructions: str, input_text: str, response_model: Type[T], schema_name: str) -> tuple[T, ModelUsage]:
        usage = ModelUsage(calls=1)
        if response_model is SourceSelection:
            data = json.loads(input_text)
            first = (data.get("results") or [{}])[0]
            return response_model(selected_url=first.get("link"), reason="mock-first-result"), usage

        data = json.loads(input_text)
        html = data.get("html", "")
        vendor = data.get("vendor_name", "Controlled Vendor")
        source_url = data.get("source_url", "")
        recipe = self._recipe_for_controlled_html(html)
        result = self._extract_for_mock(html, recipe, vendor, source_url)

        if response_model is LearnedCapabilityCandidate:
            return response_model(result=result, recipe=recipe, rationale="Mock recognized controlled DOM."), usage
        if response_model is PricingResult:
            return result, usage
        raise RuntimeError(f"Mock provider does not implement {response_model.__name__}")

    @staticmethod
    def _recipe_for_controlled_html(html: str) -> ExtractionRecipe:
        if 'data-plan-card="true"' in html:
            return ExtractionRecipe(
                fetch_mode="requests",
                container_selector='section[data-plan-card="true"]',
                plan_name=FieldRule(selector="h3.plan-title"),
                displayed_price=FieldRule(selector="span[data-current-price]"),
                billing_period=FieldRule(selector="span.billing"),
                usage_limit=FieldRule(selector="li.usage"),
            )
        if 'class="price-row"' in html:
            return ExtractionRecipe(
                fetch_mode="requests",
                container_selector="tr.price-row",
                plan_name=FieldRule(selector="td.plan"),
                displayed_price=FieldRule(selector="td.current-price"),
                billing_period=FieldRule(selector="td.period"),
                usage_limit=FieldRule(selector="td.limit"),
            )
        return ExtractionRecipe(
            fetch_mode="requests",
            container_selector="div.pricing-card",
            plan_name=FieldRule(selector="h2.plan-name"),
            displayed_price=FieldRule(selector="span.price"),
            billing_period=FieldRule(selector="span.period"),
            usage_limit=FieldRule(selector="p.usage"),
        )

    @staticmethod
    def _extract_for_mock(html: str, recipe: ExtractionRecipe, vendor: str, source_url: str) -> PricingResult:
        soup = BeautifulSoup(html, "html.parser")
        plans: list[PricePlan] = []
        for container in soup.select(recipe.container_selector):
            def txt(rule: FieldRule | None) -> str | None:
                if not rule or not rule.selector:
                    return None
                el = container.select_one(rule.selector)
                return el.get_text(" ", strip=True) if el else None
            name = txt(recipe.plan_name) or "Unknown"
            raw_price = txt(recipe.displayed_price)
            m = re.search(r"(?:\$|USD\s*)?([0-9]+(?:\.[0-9]+)?)", raw_price or "")
            price = float(m.group(1)) if m else None
            raw_period = txt(recipe.billing_period)
            p = (raw_period or "").lower()
            period = "month" if "month" in p else "year" if "year" in p or "annual" in p else None
            plans.append(PricePlan(
                plan_name=name,
                displayed_price=price,
                currency="USD" if "$" in (raw_price or "") else None,
                billing_period=period,
                usage_limit=txt(recipe.usage_limit),
            ))
        return PricingResult(vendor=vendor, retrieved_at=utc_now_iso(), plans=plans, source_url=source_url)


def provider_from_name(name: str) -> ModelProvider:
    if name.lower() == "openai":
        return OpenAIResponsesProvider()
    if name.lower() == "mock":
        return MockModelProvider()
    raise ValueError(f"Unknown provider {name!r}; supported: openai, mock")
