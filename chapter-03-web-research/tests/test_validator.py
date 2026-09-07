from pathlib import Path
from smart_agent.models import PricePlan, PricingResult, utc_now_iso
from smart_agent.validator import PricingValidator

ROOT = Path(__file__).resolve().parents[1]


def test_ground_truth_catches_wrong_price():
    result = PricingResult(
        vendor="Northstar Cloud", retrieved_at=utc_now_iso(), source_url="http://localhost/pricing",
        plans=[
            PricePlan(plan_name="Starter", displayed_price=999, currency="USD", billing_period="month", usage_limit="Up to 3 seats"),
            PricePlan(plan_name="Professional", displayed_price=49, currency="USD", billing_period="month", usage_limit="Up to 15 seats"),
            PricePlan(plan_name="Business", displayed_price=99, currency="USD", billing_period="month", usage_limit="Up to 50 seats"),
        ],
    )
    validation = PricingValidator().validate_against_ground_truth(result, ROOT / "benchmark_site/ground_truth/v1.json")
    assert not validation.passed
    assert any("DISPLAYED_PRICE" in issue.code for issue in validation.issues)
