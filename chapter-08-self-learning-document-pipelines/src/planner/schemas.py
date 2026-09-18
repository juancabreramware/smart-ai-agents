from __future__ import annotations

SEMANTIC_LABELS = [
    "none", "pricing_dispute", "quantity_dispute",
    "address_exception", "tax_exception", "other",
]

_STRING = {"type": "string"}

FIELD_SCHEMAS = {
    "invoice.northstar": {
        "invoice_number": _STRING, "vendor_id": _STRING, "invoice_date": _STRING,
        "due_date": _STRING, "po_number": _STRING, "subtotal": _STRING,
        "tax": _STRING, "total": _STRING, "currency": _STRING,
    },
    "invoice.redwood": {
        "invoice_number": _STRING, "account_number": _STRING, "invoice_date": _STRING,
        "service_period": _STRING, "subtotal": _STRING, "fees": _STRING,
        "tax": _STRING, "total": _STRING, "currency": _STRING,
    },
    "purchase_order.harborpoint": {
        "po_number": _STRING, "supplier_id": _STRING, "order_date": _STRING,
        "buyer": _STRING, "ship_to": _STRING,
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "sku": {"type": "string"},
                    "quantity": {"type": "integer"},
                    "unit_price": {"type": "string"},
                },
                "required": ["sku", "quantity", "unit_price"],
            },
        },
        "subtotal": _STRING, "total": _STRING,
    },
    "shipping_notice.blueriver": {
        "shipment_id": _STRING, "carrier": _STRING, "tracking_number": _STRING,
        "po_number": _STRING, "ship_date": _STRING, "expected_delivery": _STRING,
        "package_count": _STRING,
    },
    "remittance.meridian": {
        "payment_id": _STRING, "payment_date": _STRING, "payer": _STRING,
        "invoice_references": {"type": "array", "items": {"type": "string"}},
        "gross_amount": _STRING, "deductions": _STRING, "net_amount": _STRING,
    },
    "tax_form.w9": {
        "legal_name": _STRING, "business_name": _STRING,
        "tax_classification": _STRING, "address": _STRING,
        "tin_type": _STRING, "masked_tin": _STRING,
    },
}


def extraction_response_schema(family: str, required_fields: list[str]) -> dict:
    """Build the strict Structured Outputs schema for one document family."""
    if family not in FIELD_SCHEMAS:
        raise ValueError(f"unknown_document_family:{family}")
    known = FIELD_SCHEMAS[family]
    missing = [name for name in required_fields if name not in known]
    if missing:
        raise ValueError(f"missing_field_schema:{family}:{','.join(missing)}")
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "family_id": {"type": "string", "enum": [family]},
            "fields": {
                "type": "object",
                "additionalProperties": False,
                "properties": {name: known[name] for name in required_fields},
                "required": list(required_fields),
            },
            "semantic_label": {
                "type": ["string", "null"],
                "enum": SEMANTIC_LABELS + [None],
            },
        },
        "required": ["family_id", "fields", "semantic_label"],
    }


def validate_strict_schema(schema: dict) -> None:
    """Offline guard for the strict-schema mistakes that caused demo-real-v1 to fail."""
    def walk(node: dict, path: str) -> None:
        if not isinstance(node, dict):
            raise ValueError(f"schema_node_not_object:{path}")
        if "type" not in node:
            raise ValueError(f"schema_missing_type:{path}")
        types = node["type"] if isinstance(node["type"], list) else [node["type"]]
        if "object" in types:
            if node.get("additionalProperties") is not False:
                raise ValueError(f"object_must_forbid_additional_properties:{path}")
            props = node.get("properties")
            if not isinstance(props, dict):
                raise ValueError(f"object_missing_properties:{path}")
            if set(node.get("required", [])) != set(props):
                raise ValueError(f"strict_object_requires_all_properties:{path}")
            for name, child in props.items():
                walk(child, f"{path}.{name}")
        if "array" in types:
            items = node.get("items")
            if not isinstance(items, dict):
                raise ValueError(f"array_missing_items:{path}")
            walk(items, f"{path}[]")
    walk(schema, "$")
