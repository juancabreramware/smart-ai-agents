"""Trusted deterministic executor for model-learned extraction recipes.

The model may learn selectors and optional regexes, but this module owns canonical semantic
normalization. That division is deliberate: the LLM discovers *where* the data lives while
ordinary software handles stable transformations such as ``per month`` -> ``month``.
"""

from __future__ import annotations

import re
from bs4 import BeautifulSoup, Tag

from .models import ExtractionRecipe, FieldRule, PricePlan, PricingResult, utc_now_iso
from .normalizer import normalize_billing_period, normalize_currency, normalize_price_value, normalize_pricing_result


def _read_rule(container: Tag, rule: FieldRule | None) -> str | None:
    """Read one field from a plan container according to a constrained recipe rule."""
    if not rule or not rule.selector:
        return None
    element = container.select_one(rule.selector)
    if element is None:
        return None
    value = element.get_text(" ", strip=True) if rule.attribute == "text" else element.get(rule.attribute)
    if value is None:
        return None
    value = str(value).strip()
    if rule.regex:
        match = re.search(rule.regex, value)
        if not match:
            return None
        value = match.group(1) if match.lastindex else match.group(0)
    return value.strip()


def normalize_price(raw: str | None) -> tuple[float | None, str | None]:
    """Backward-compatible helper used by tests/readers from v1.0.

    Price and currency are now delegated to the shared canonical normalizer so both the
    model-produced result and deterministic artifact follow the same semantic rules.
    """
    return normalize_price_value(raw), normalize_currency(raw)


def normalize_period(raw: str | None) -> str | None:
    """Backward-compatible alias for the shared billing-period normalizer."""
    return normalize_billing_period(raw)


class DeterministicPricingExtractor:
    """Interpret a promoted recipe against freshly retrieved HTML.

    Important: the artifact never stores today's price. It stores the procedure for finding
    the current price. Each execution therefore retrieves fresh source data while avoiding
    repeated LLM discovery work.
    """

    def execute(self, *, html: str, recipe: ExtractionRecipe, vendor_name: str, source_url: str) -> PricingResult:
        soup = BeautifulSoup(html, "html.parser")
        plans: list[PricePlan] = []

        for container in soup.select(recipe.container_selector):
            name = (_read_rule(container, recipe.plan_name) or "").strip()
            raw_price = _read_rule(container, recipe.displayed_price)

            # First infer currency from the complete displayed-price text. This is why the
            # prompts tell the model NOT to strip "$"/"USD" from the price selector.
            price = normalize_price_value(raw_price)
            currency = normalize_currency(raw_price)

            # Some real sites render <amount>49</amount> and <currency>USD</currency> in
            # separate elements. A learned recipe can explicitly point at that second field.
            if currency is None:
                currency = normalize_currency(_read_rule(container, recipe.currency))

            plans.append(
                PricePlan(
                    plan_name=name,
                    displayed_price=price,
                    currency=currency,
                    billing_period=normalize_billing_period(_read_rule(container, recipe.billing_period)),
                    usage_limit=_read_rule(container, recipe.usage_limit),
                )
            )

        # Run the final structure through the SAME normalizer used for model-direct output.
        # This makes promotion comparisons symmetric and prevents representational trivia
        # from masquerading as an architecture failure.
        return normalize_pricing_result(
            PricingResult(
                vendor=vendor_name,
                retrieved_at=utc_now_iso(),
                plans=plans,
                source_url=source_url,
            )
        )
