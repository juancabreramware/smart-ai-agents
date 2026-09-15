from __future__ import annotations

from dataclasses import dataclass, field
from copy import deepcopy
from typing import Any


def _initial_orders() -> dict[str, dict[str, Any]]:
    statuses = ["PICKING", "PACKED", "SHIPPED", "DELIVERED"]
    return {
        f"ORD-{i:04d}": {"status": statuses[i % len(statuses)]}
        for i in range(1, 41)
    }


def _initial_customers() -> dict[str, dict[str, Any]]:
    return {
        f"CUS-{i:04d}": {
            "email": f"ops{i}@example.test",
            "phone": f"407555{i:04d}"[-10:],
        }
        for i in range(1, 41)
    }


@dataclass(slots=True)
class PortalState:
    ui_version: str = "V1"
    orders: dict[str, dict[str, Any]] = field(default_factory=_initial_orders)
    customers: dict[str, dict[str, Any]] = field(default_factory=_initial_customers)
    shipping: dict[str, dict[str, str]] = field(default_factory=dict)
    credits: list[dict[str, Any]] = field(default_factory=list)
    returns: list[dict[str, Any]] = field(default_factory=list)
    reservations: list[dict[str, Any]] = field(default_factory=list)

    def reset(self) -> None:
        fresh = PortalState()
        self.ui_version = fresh.ui_version
        self.orders = fresh.orders
        self.customers = fresh.customers
        self.shipping.clear()
        self.credits.clear()
        self.returns.clear()
        self.reservations.clear()

    def snapshot(self) -> dict[str, Any]:
        return deepcopy({
            "ui_version": self.ui_version,
            "orders": self.orders,
            "customers": self.customers,
            "shipping": self.shipping,
            "credits": self.credits,
            "returns": self.returns,
            "reservations": self.reservations,
        })
