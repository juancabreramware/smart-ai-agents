from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .model import UICapability


class CapabilityRegistry:
    def __init__(self):
        self._versions: dict[str, list[UICapability]] = defaultdict(list)

    def active(self, operation_family: str) -> UICapability | None:
        for cap in reversed(self._versions.get(operation_family, [])):
            if cap.validation_state == "VALIDATED" and cap.superseded_by is None:
                return cap
        return None

    def all(self) -> list[UICapability]:
        return [cap for versions in self._versions.values() for cap in versions]

    def promote(self, capability: UICapability) -> UICapability:
        versions = self._versions[capability.operation_family]
        previous = versions[-1] if versions else None
        if previous is not None:
            if previous.validation_state == "VALIDATED":
                previous.validation_state = "SUPERSEDED"
            previous.superseded_by = capability.capability_id
        versions.append(capability)
        return capability

    def invalidate(self, capability: UICapability, reason: str) -> None:
        capability.validation_state = "INVALIDATED"
        capability.failure_count += 1
        capability.provenance.setdefault("invalidations", []).append(reason)

    def next_version(self, operation_family: str) -> int:
        return len(self._versions.get(operation_family, [])) + 1

    def snapshot(self) -> list[dict]:
        return [c.to_dict() for c in self.all()]
