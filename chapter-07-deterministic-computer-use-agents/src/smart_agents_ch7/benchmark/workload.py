from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import BenchmarkRequest

FAMILIES = [
    "orders.lookup_status",
    "shipping.update_instructions",
    "billing.apply_credit",
    "returns.create_authorization",
    "customers.update_contact",
    "inventory.reserve_stock",
]
AFFECTED_V2 = {
    "shipping.update_instructions",
    "billing.apply_credit",
    "returns.create_authorization",
    "inventory.reserve_stock",
}


def _args(family: str, n: int, ui_version: str) -> dict:
    idx = ((n - 1) % 40) + 1
    order_id = f"ORD-{idx:04d}"
    customer_id = f"CUS-{idx:04d}"
    if family == "orders.lookup_status":
        return {"order_id": order_id}
    if family == "shipping.update_instructions":
        return {
            "order_id": order_id,
            "delivery_window": f"{8 + (idx % 5)}:00-{12 + (idx % 5)}:00",
            "instructions": f"Dock {1 + (idx % 7)}; reference request {n}",
        }
    if family == "billing.apply_credit":
        amount = [25.00, 49.50, 75.00, 125.00, 180.25][idx % 5]
        return {
            "customer_id": customer_id,
            "amount": amount,
            "amount_cents": int(round(amount * 100)),
            "reason_code": ["SERVICE", "SHIPPING", "GOODWILL"][idx % 3],
            "approval_code": f"APR-{n:04d}",
        }
    if family == "returns.create_authorization":
        return {
            "order_id": order_id,
            "item_sku": f"SKU-{100 + (idx % 15)}",
            "reason": ["DAMAGED", "WRONG_ITEM", "OTHER"][idx % 3],
        }
    if family == "customers.update_contact":
        return {
            "customer_id": customer_id,
            "email": f"harborpoint-{n}@example.test",
            "phone": f"407{(7000000 + n):07d}"[-10:],
        }
    if family == "inventory.reserve_stock":
        return {
            "sku": f"SKU-{100 + (idx % 15)}",
            "location": f"LOC-{1 + (idx % 6):02d}",
            "quantity": 1 + (idx % 8),
        }
    raise ValueError(family)


def build_benchmark() -> list[BenchmarkRequest]:
    requests: list[BenchmarkRequest] = []
    n = 1

    # Phase A: 60 V1 requests, 10 per operation family.
    for _round in range(10):
        for family in FAMILIES:
            requests.append(BenchmarkRequest(
                request_id=f"CH7-{n:03d}", phase="A", ui_version="V1",
                operation_family=family, args=_args(family, n, "V1"),
                reasoning_required=False, v2_affected=False,
            ))
            n += 1

    # Phase B: 30 V1 requests, 5 per family. Three of each family are deliberately
    # marked reasoning-required to preserve genuine runtime reasoning in the workload.
    for family in FAMILIES:
        for j in range(5):
            requests.append(BenchmarkRequest(
                request_id=f"CH7-{n:03d}", phase="B", ui_version="V1",
                operation_family=family, args=_args(family, n, "V1"),
                reasoning_required=(j < 3), v2_affected=False,
            ))
            n += 1

    # Phase C: 60 V2 requests. Four changed families receive 8 requests each;
    # the two unchanged families receive 14 each. This explicitly tests selective
    # invalidation without globally flushing the registry.
    for family in FAMILIES:
        count = 8 if family in AFFECTED_V2 else 14
        for _ in range(count):
            requests.append(BenchmarkRequest(
                request_id=f"CH7-{n:03d}", phase="C", ui_version="V2",
                operation_family=family, args=_args(family, n, "V2"),
                reasoning_required=False, v2_affected=(family in AFFECTED_V2),
            ))
            n += 1

    assert len(requests) == 150
    assert requests[89].request_id == "CH7-090"
    assert requests[90].request_id == "CH7-091"
    return requests


def build_demo() -> list[BenchmarkRequest]:
    # Human-readable sequence: acquire six capabilities, reuse three, then switch to V2
    # and exercise four changed plus two unchanged families.
    sequence = [
        ("V1", "orders.lookup_status"),
        ("V1", "shipping.update_instructions"),
        ("V1", "billing.apply_credit"),
        ("V1", "returns.create_authorization"),
        ("V1", "customers.update_contact"),
        ("V1", "inventory.reserve_stock"),
        ("V1", "orders.lookup_status"),
        ("V1", "billing.apply_credit"),
        ("V1", "inventory.reserve_stock"),
        ("V2", "shipping.update_instructions"),
        ("V2", "billing.apply_credit"),
        ("V2", "returns.create_authorization"),
        ("V2", "inventory.reserve_stock"),
        ("V2", "orders.lookup_status"),
        ("V2", "customers.update_contact"),
    ]
    result = []
    for i, (version, family) in enumerate(sequence, 1):
        result.append(BenchmarkRequest(
            request_id=f"DEMO-{i:02d}",
            phase="A" if i <= 9 else "C",
            ui_version=version,
            operation_family=family,
            args=_args(family, 200+i, version),
            reasoning_required=False,
            v2_affected=(version == "V2" and family in AFFECTED_V2),
        ))
    return result


def write_jsonl(path: Path, requests: Iterable[BenchmarkRequest]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for req in requests:
            f.write(json.dumps(req.to_dict(), sort_keys=True) + "\n")


def load_jsonl(path: Path) -> list[BenchmarkRequest]:
    with path.open("r", encoding="utf-8") as f:
        return [BenchmarkRequest.from_dict(json.loads(line)) for line in f if line.strip()]
