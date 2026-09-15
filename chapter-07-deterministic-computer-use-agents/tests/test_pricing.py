from smart_agents_ch7.benchmark.pricing import Pricing
from smart_agents_ch7.planner.models import TokenUsage


def test_pricing_separates_cached_input():
    pricing = Pricing(input_per_million=4.0, cached_input_per_million=0.4, output_per_million=20.0)
    usage = TokenUsage(input_tokens=1000, cached_input_tokens=400, output_tokens=100)
    expected = (600*4 + 400*0.4 + 100*20) / 1_000_000
    assert abs(pricing.cost(usage) - expected) < 1e-12
