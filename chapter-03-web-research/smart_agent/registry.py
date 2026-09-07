"""File-backed Capability Registry.

JSON is deliberate here: readers can inspect every capability version with a text editor
and see what Executable Memory actually looks like.
"""

from __future__ import annotations

import re
from pathlib import Path

from .models import CapabilityRecord, CapabilityStatus, ExtractionRecipe, utc_now_iso
from .settings import settings


class CapabilityRegistry:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or settings.capability_dir
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def capability_id(vendor_id: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", vendor_id).strip("-").lower()
        return f"cap_saas_pricing_{safe}"

    def _path(self, capability_id: str, version: int) -> Path:
        return self.root / f"{capability_id}.v{version}.json"

    def list_versions(self, capability_id: str) -> list[CapabilityRecord]:
        rows = [CapabilityRecord.model_validate_json(p.read_text(encoding="utf-8")) for p in self.root.glob(f"{capability_id}.v*.json")]
        return sorted(rows, key=lambda x: x.version)

    def latest_active(self, vendor_id: str) -> CapabilityRecord | None:
        active = [r for r in self.list_versions(self.capability_id(vendor_id)) if r.status == CapabilityStatus.ACTIVE]
        return active[-1] if active else None

    def create_or_upgrade(self, *, vendor_id: str, source_url: str, recipe: ExtractionRecipe, task_signature: dict, parent_version: int | None = None) -> CapabilityRecord:
        cid = self.capability_id(vendor_id)
        versions = self.list_versions(cid)
        next_version = versions[-1].version + 1 if versions else 1
        # Keep old versions for audit/rollback, but only the newest promoted one remains active.
        for old in versions:
            if old.status == CapabilityStatus.ACTIVE:
                old.status = CapabilityStatus.DISABLED
                self.save(old)
        record = CapabilityRecord(
            capability_id=cid,
            version=next_version,
            status=CapabilityStatus.ACTIVE,
            task_signature=task_signature,
            source_url=source_url,
            recipe=recipe,
            parent_version=parent_version,
            last_validated_at=utc_now_iso(),
        )
        self.save(record)
        return record

    def save(self, record: CapabilityRecord) -> None:
        path = self._path(record.capability_id, record.version)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        tmp.replace(path)

    def mark_success(self, record: CapabilityRecord) -> None:
        record.successes += 1
        record.last_validated_at = utc_now_iso()
        self.save(record)

    def mark_failure(self, record: CapabilityRecord) -> None:
        record.failures += 1
        record.fallback_count += 1
        record.status = CapabilityStatus.DEGRADED
        self.save(record)

    def reset(self) -> None:
        for path in self.root.glob("*.json"):
            path.unlink()
