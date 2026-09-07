from pathlib import Path
from smart_agent.extractor import DeterministicPricingExtractor
from smart_agent.model_provider import MockModelProvider
from smart_agent.validator import PricingValidator

ROOT = Path(__file__).resolve().parents[1]


def test_v1_recipe_extracts_ground_truth():
    html = (ROOT / "benchmark_site/v1/pricing.html").read_text()
    recipe = MockModelProvider()._recipe_for_controlled_html(html)
    result = DeterministicPricingExtractor().execute(
        html=html, recipe=recipe, vendor_name="Northstar Cloud", source_url="http://localhost/pricing"
    )
    validation = PricingValidator().validate_against_ground_truth(result, ROOT / "benchmark_site/ground_truth/v1.json")
    assert validation.passed, validation.issues


def test_v1_recipe_breaks_on_v2():
    v1 = (ROOT / "benchmark_site/v1/pricing.html").read_text()
    v2 = (ROOT / "benchmark_site/v2/pricing.html").read_text()
    recipe = MockModelProvider()._recipe_for_controlled_html(v1)
    result = DeterministicPricingExtractor().execute(
        html=v2, recipe=recipe, vendor_name="Northstar Cloud", source_url="http://localhost/pricing"
    )
    validation = PricingValidator().validate_against_ground_truth(result, ROOT / "benchmark_site/ground_truth/v2.json")
    assert not validation.passed


def test_v2_recipe_extracts_ground_truth():
    html = (ROOT / "benchmark_site/v2/pricing.html").read_text()
    recipe = MockModelProvider()._recipe_for_controlled_html(html)
    result = DeterministicPricingExtractor().execute(
        html=html, recipe=recipe, vendor_name="Northstar Cloud", source_url="http://localhost/pricing"
    )
    validation = PricingValidator().validate_against_ground_truth(result, ROOT / "benchmark_site/ground_truth/v2.json")
    assert validation.passed, validation.issues


def test_recipe_can_extract_currency_from_separate_element():
    """Some real pages render amount and currency independently; v1.1 supports that."""
    from smart_agent.models import ExtractionRecipe, FieldRule

    html = """
    <div class="plan-card">
      <h2>Starter</h2>
      <span class="amount">49</span>
      <span class="currency">USD</span>
      <span class="period">per month</span>
    </div>
    """
    recipe = ExtractionRecipe(
        fetch_mode="requests",
        container_selector="div.plan-card",
        plan_name=FieldRule(selector="h2"),
        displayed_price=FieldRule(selector="span.amount"),
        currency=FieldRule(selector="span.currency"),
        billing_period=FieldRule(selector="span.period"),
    )
    result = DeterministicPricingExtractor().execute(
        html=html,
        recipe=recipe,
        vendor_name="Example",
        source_url="http://localhost/pricing",
    )
    plan = result.plans[0]
    assert plan.displayed_price == 49.0
    assert plan.currency == "USD"
    assert plan.billing_period == "month"


def test_full_price_text_preserves_currency_without_separate_rule():
    """The preferred recipe keeps '$49' intact so currency can be inferred cheaply."""
    from smart_agent.models import ExtractionRecipe, FieldRule

    html = """
    <div class="plan-card">
      <h2>Starter</h2>
      <span class="price">$49</span>
      <span class="period">monthly</span>
    </div>
    """
    recipe = ExtractionRecipe(
        fetch_mode="requests",
        container_selector="div.plan-card",
        plan_name=FieldRule(selector="h2"),
        displayed_price=FieldRule(selector="span.price"),
        billing_period=FieldRule(selector="span.period"),
    )
    result = DeterministicPricingExtractor().execute(
        html=html,
        recipe=recipe,
        vendor_name="Example",
        source_url="http://localhost/pricing",
    )
    plan = result.plans[0]
    assert plan.displayed_price == 49.0
    assert plan.currency == "USD"
    assert plan.billing_period == "month"
