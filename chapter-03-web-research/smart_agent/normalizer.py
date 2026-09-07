"""Trusted semantic normalization shared by BOTH Chapter 3 architectures.

Why this module exists
----------------------
A model may correctly read ``per month`` while the experiment's canonical schema expects
``month``. Likewise, one extraction recipe may see ``$49`` while another sees the amount
and currency in separate DOM elements. Those are representation differences, not reasoning
problems.

The architecture should therefore not ask an LLM to repeatedly solve stable formatting
rules that ordinary software can handle. This module is the single deterministic boundary
that converts semantically equivalent representations into one canonical form before
validation and comparison.

Keeping this code shared is important to experimental fairness: the Reasoning-First baseline
and the Smart Agent are judged through exactly the same canonicalization rules.
"""

from __future__ import annotations

import re

from .models import PricePlan, PricingResult


# Small, explicit mapping for the currencies the Chapter 3 experiment understands.
# The code intentionally does not pretend to be a global foreign-exchange library.
_CURRENCY_ALIASES = {
    "$": "USD",
    "US$": "USD",
    "USD": "USD",
    "€": "EUR",
    "EUR": "EUR",
    "£": "GBP",
    "GBP": "GBP",
}


def normalize_currency(raw: str | None) -> str | None:
    """Return a canonical ISO-ish currency code for a small known set.

    The function accepts either a bare code/symbol (``USD`` / ``$``) or a larger piece
    of text containing one (``$49 per month``). Unknown currencies are preserved as an
    upper-case string only when the input itself looks like a three-letter code; otherwise
    we return ``None`` rather than inventing meaning.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None

    upper = text.upper()
    # Prefer explicit three-letter codes when present in surrounding text.
    for code in ("USD", "EUR", "GBP"):
        if re.search(rf"\b{code}\b", upper):
            return code

    # Symbols are useful when the source displays "$49" rather than "USD 49".
    if "US$" in upper or "$" in text:
        return "USD"
    if "€" in text:
        return "EUR"
    if "£" in text:
        return "GBP"

    # A bare three-letter value may be a currency code the benchmark does not know yet.
    # Preserve it rather than silently dropping potentially useful structured data.
    if re.fullmatch(r"[A-Za-z]{3}", text):
        return upper
    return _CURRENCY_ALIASES.get(text)


def normalize_billing_period(raw: str | None) -> str | None:
    """Canonicalize common billing-period wording.

    Examples:
        ``per month`` / ``monthly`` / ``/mo`` -> ``month``
        ``per year`` / ``annually`` / ``/yr`` -> ``year``
        ``one time``                         -> ``one_time``

    The checks are intentionally conservative. If we cannot confidently map the phrase,
    returning ``None`` forces validation to decide whether the missing semantic value is
    acceptable instead of fabricating one.
    """
    if raw is None:
        return None
    text = str(raw).strip().lower()
    if not text:
        return None

    # Test annual forms before very broad substring checks.
    annual_patterns = (
        r"\bper\s+(?:year|yr)\b",
        r"/(?:year|yr)\b",
        r"\bannual(?:ly)?\b",
        r"\byearly\b",
        r"\b(?:year|yr)\b",
    )
    if any(re.search(p, text) for p in annual_patterns):
        return "year"

    monthly_patterns = (
        r"\bper\s+(?:month|mo)\b",
        r"/(?:month|mo)\b",
        r"\bmonthly\b",
        r"\b(?:month|mo)\b",
    )
    if any(re.search(p, text) for p in monthly_patterns):
        return "month"

    if re.search(r"\bone[-\s]?time\b", text) or "single payment" in text:
        return "one_time"
    return None


def normalize_price_value(raw: str | float | int | None) -> float | None:
    """Convert a numeric price or displayed-price string into a float.

    ``Contact Sales`` and similar non-numeric prices remain ``None``. The normalizer does
    not interpret discounts or do arithmetic; it merely canonicalizes the selected value.
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)

    text = str(raw).strip()
    if not text:
        return None
    low = text.lower()
    if any(word in low for word in ("contact", "custom", "call us")):
        return None

    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", text.replace(",", ""))
    return float(match.group(1)) if match else None


def normalize_plan(plan: PricePlan) -> PricePlan:
    """Return a normalized copy of one plan without mutating caller-owned data."""
    return PricePlan(
        plan_name=(plan.plan_name or "").strip(),
        displayed_price=normalize_price_value(plan.displayed_price),
        currency=normalize_currency(plan.currency),
        billing_period=normalize_billing_period(plan.billing_period),
        usage_limit=plan.usage_limit.strip() if isinstance(plan.usage_limit, str) else plan.usage_limit,
        notes=plan.notes.strip() if isinstance(plan.notes, str) else plan.notes,
    )


def normalize_pricing_result(result: PricingResult) -> PricingResult:
    """Canonicalize a full result while preserving retrieval/source metadata."""
    return PricingResult(
        vendor=result.vendor.strip(),
        retrieved_at=result.retrieved_at,
        plans=[normalize_plan(plan) for plan in result.plans],
        source_url=result.source_url,
    )
