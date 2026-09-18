import pytest
from src.documents.contracts import required_fields
from src.planner.schemas import FIELD_SCHEMAS, extraction_response_schema, validate_strict_schema


def test_all_family_contract_schemas_are_strict_and_typed():
    for version in ("V1", "V2"):
        for family in FIELD_SCHEMAS:
            schema = extraction_response_schema(family, required_fields(family, version))
            validate_strict_schema(schema)
            for name, field_schema in schema["properties"]["fields"]["properties"].items():
                assert "type" in field_schema, (family, version, name)


def test_purchase_order_line_items_are_nested_and_typed():
    schema = extraction_response_schema(
        "purchase_order.harborpoint",
        required_fields("purchase_order.harborpoint", "V1"),
    )
    line_items = schema["properties"]["fields"]["properties"]["line_items"]
    assert line_items["type"] == "array"
    item = line_items["items"]
    assert item["type"] == "object"
    assert item["additionalProperties"] is False
    assert item["properties"]["quantity"]["type"] == "integer"


def test_remittance_invoice_references_are_string_array():
    schema = extraction_response_schema(
        "remittance.meridian",
        required_fields("remittance.meridian", "V2"),
    )
    refs = schema["properties"]["fields"]["properties"]["invoice_references"]
    assert refs == {"type": "array", "items": {"type": "string"}}


def test_offline_validator_rejects_untyped_property():
    bad = {
        "type": "object", "additionalProperties": False,
        "properties": {"invoice_number": {}},
        "required": ["invoice_number"],
    }
    with pytest.raises(ValueError, match="schema_missing_type"):
        validate_strict_schema(bad)
