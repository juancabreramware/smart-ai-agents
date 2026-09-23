import hashlib
import json

from src.contracts import (
    PUBLIC_OPERATIONAL_CONTRACTS,
    PUBLIC_OPERATIONAL_CONTRACT_VERSION,
    public_operational_contract_manifest,
)


def _hash_json(obj):
    return hashlib.sha256(
        json.dumps(
            obj,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def test_provider_contract_version_is_v104():
    assert (
        PUBLIC_OPERATIONAL_CONTRACT_VERSION
        == "chapter12-provider-contract-v1.0.4"
    )


def test_provider_contract_manifest_covers_registry_exactly():
    manifest = public_operational_contract_manifest()

    actual = {
        (row["family"], row["version"])
        for row in manifest["contracts"]
    }

    assert actual == set(PUBLIC_OPERATIONAL_CONTRACTS)
    assert len(actual) == len(manifest["contracts"])


def test_provider_contract_manifest_contains_exact_contract_text():
    manifest = public_operational_contract_manifest()

    for row in manifest["contracts"]:
        key = (row["family"], row["version"])
        assert row["contract"] == PUBLIC_OPERATIONAL_CONTRACTS[key]


def test_provider_contract_hash_is_deterministic():
    first = _hash_json(public_operational_contract_manifest())
    second = _hash_json(public_operational_contract_manifest())

    assert first == second
    assert len(first) == 64
