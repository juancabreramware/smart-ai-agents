from pathlib import Path
from smart_agent.model_provider import MockModelProvider
from smart_agent.registry import CapabilityRegistry


def test_registry_versions_and_disables_old_active(tmp_path: Path):
    registry = CapabilityRegistry(tmp_path)
    html = '<div class="pricing-card"><h2 class="plan-name">A</h2><span class="price">$1</span></div>'
    recipe = MockModelProvider()._recipe_for_controlled_html(html)
    v1 = registry.create_or_upgrade(
        vendor_id="vendor", source_url="http://localhost/pricing", recipe=recipe,
        task_signature={"task_type": "saas_pricing_research"}
    )
    v2 = registry.create_or_upgrade(
        vendor_id="vendor", source_url="http://localhost/pricing", recipe=recipe,
        task_signature={"task_type": "saas_pricing_research"}, parent_version=1
    )
    assert v1.version == 1 and v2.version == 2
    assert registry.latest_active("vendor").version == 2
    versions = registry.list_versions(v1.capability_id)
    assert versions[0].status.value == "DISABLED"
    assert versions[1].status.value == "ACTIVE"
