from smart_agents_ch7.portal.contracts import V1, V2


def test_selective_contract_drift():
    unchanged = {"orders.lookup_status", "customers.update_contact"}
    changed = set(V1) - unchanged
    for family in unchanged:
        assert V1[family].fingerprint() == V2[family].fingerprint()
        assert V1[family].family_contract_version == V2[family].family_contract_version == "v1"
    for family in changed:
        assert V1[family].fingerprint() != V2[family].fingerprint()
        assert V2[family].family_contract_version == "v2"
