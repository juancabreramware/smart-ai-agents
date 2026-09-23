from src.contracts import (
    PUBLIC_OPERATIONAL_CONTRACTS,
    public_operational_contract,
)
from src.workload import build


def test_every_canonical_request_has_public_contract():
    for request in build():
        contract = public_operational_contract(
            request.family,
            request.version,
        )
        assert isinstance(contract, str)
        assert contract.strip()


def test_public_contract_registry_has_expected_versions():
    expected = {
        ("stable_recurring", 1),
        ("stable_rare", 1),
        ("volatile_recurring", 1),
        ("volatile_recurring", 2),
        ("volatile_recurring", 3),
        ("high_validation_recurring", 1),
        ("ambiguous_judgment", 1),
        ("emerging_pattern", 1),
    }

    assert set(PUBLIC_OPERATIONAL_CONTRACTS) == expected


def test_public_contracts_do_not_contain_future_benchmark_information():
    forbidden = (
        "future_count",
        "remaining_requests",
        "next_drift",
        "future_drift",
        "benchmark_remainder",
        "ground_truth",
        "expected_answer",
    )

    for contract in PUBLIC_OPERATIONAL_CONTRACTS.values():
        lowered = contract.lower()
        for term in forbidden:
            assert term not in lowered


def test_openai_provider_uses_public_contract_not_ground_truth():
    from pathlib import Path

    source = Path("src/provider.py").read_text(encoding="utf-8-sig")

    assert "class OpenAIProvider:" in source

    openai_source = source.split("class OpenAIProvider:", 1)[1]

    assert "ground_truth(" not in openai_source
    assert (
        "public_operational_contract(r.family, r.version)"
        in openai_source
    )
