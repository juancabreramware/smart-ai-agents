"""Regression tests added after the first real-model Chapter 3 run.

The mock provider had hidden two assumptions:
1. the model may say "per month" while ground truth says "month";
2. a recipe may separate amount from currency.
These tests preserve the fixes as executable documentation.
"""

from smart_agent.models import PricePlan, PricingResult, utc_now_iso
from smart_agent.normalizer import (
    normalize_billing_period,
    normalize_currency,
    normalize_pricing_result,
)


def test_common_monthly_phrases_normalize_to_month():
    for raw in ("per month", "/month", "/mo", "monthly", "month"):
        assert normalize_billing_period(raw) == "month"


def test_common_annual_phrases_normalize_to_year():
    for raw in ("per year", "/year", "/yr", "annually", "annual", "yearly"):
        assert normalize_billing_period(raw) == "year"


def test_one_time_normalization():
    assert normalize_billing_period("one-time") == "one_time"
    assert normalize_billing_period("one time") == "one_time"


def test_currency_can_be_derived_from_symbol_or_code():
    assert normalize_currency("$49 per month") == "USD"
    assert normalize_currency("USD 49") == "USD"
    assert normalize_currency("€29") == "EUR"
    assert normalize_currency("GBP") == "GBP"


def test_model_direct_result_uses_same_canonical_normalization():
    raw = PricingResult(
        vendor="Northstar Cloud",
        retrieved_at=utc_now_iso(),
        source_url="http://localhost/pricing",
        plans=[
            PricePlan(
                plan_name="Starter",
                displayed_price=19,
                currency="usd",
                billing_period="per month",
                usage_limit="Up to 3 seats",
            )
        ],
    )
    normalized = normalize_pricing_result(raw)
    assert normalized.plans[0].currency == "USD"
    assert normalized.plans[0].billing_period == "month"
