from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from smart_agents_ch7.benchmark.models import BenchmarkRequest
from smart_agents_ch7.portal.contracts import UIContract
from .model import UICapability


@dataclass(slots=True)
class CompatibilityResult:
    ok: bool
    reasons: list[str]
    checks: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check_compatibility(cap: UICapability, request: BenchmarkRequest, contract: UIContract) -> CompatibilityResult:
    checks = {
        "operation_family": cap.operation_family == request.operation_family,
        "validation_state": cap.validation_state == "VALIDATED" and cap.superseded_by is None,
        "ui_contract_version": cap.ui_contract_version == contract.family_contract_version,
        "contract_fingerprint": cap.contract_fingerprint == contract.fingerprint(),
        "route": cap.plan.start_path == contract.route,
        "required_args": all(k in request.args and request.args[k] not in (None, "") for k in cap.plan.required_args),
        "postcondition": bool(cap.plan.postcondition),
    }
    reasons = [name for name, passed in checks.items() if not passed]
    return CompatibilityResult(not reasons, reasons, checks)
