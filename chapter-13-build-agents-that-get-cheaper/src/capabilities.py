from __future__ import annotations
import hashlib, json
from .models import Request, ProviderResult, ValidatedCapability
from .contracts import OPERATION_BY_FAMILY, contract_hash
from .runtime import validate_candidate

POLICY_VERSION="chapter13-capability-policy-v1.0.0"
MIN_OBSERVATIONS_TO_PROMOTE=2
ENVIRONMENT_FINGERPRINT="chapter13-controlled-runtime-v1"
DEPENDENCY_FINGERPRINT="chapter13-stdlib-only-runtime-v1"
VALIDATION_SUITE_ID="chapter13-operation-validation-v1"

def _h(obj)->str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()

POLICY_HASH=_h({"version":POLICY_VERSION,"min_observations_to_promote":MIN_OBSERVATIONS_TO_PROMOTE})

def compatible(cap:ValidatedCapability,r:Request)->bool:
    return (
        cap.family==r.family
        and cap.contract_version==r.version
        and cap.operation==OPERATION_BY_FAMILY[r.family]
        and cap.policy_fingerprint==POLICY_HASH
        and cap.environment_fingerprint==ENVIRONMENT_FINGERPRINT
        and cap.dependency_fingerprint==DEPENDENCY_FINGERPRINT
        and cap.validation_status=="passed"
    )

def promote(r:Request,result:ProviderResult)->ValidatedCapability|None:
    if not validate_candidate(result.operation,r,result.answer):
        return None
    impl_hash=_h({"operation":result.operation,"family":r.family,"version":r.version,"contract_hash":contract_hash()})
    return ValidatedCapability(
        capability_id=f"{r.family}:{r.version}",
        family=r.family, operation=result.operation, contract_version=r.version,
        input_schema=f"{r.family}.input.v1",output_schema="boolean",
        implementation_hash=impl_hash,
        dependency_fingerprint=DEPENDENCY_FINGERPRINT,
        policy_fingerprint=POLICY_HASH,
        environment_fingerprint=ENVIRONMENT_FINGERPRINT,
        validation_suite_id=VALIDATION_SUITE_ID,
        validation_status="passed",
        provenance={"source":"validated_provider_reasoning","request_id":r.request_id},
        acquired_at_sequence=r.sequence,last_validated_sequence=r.sequence,
    )
