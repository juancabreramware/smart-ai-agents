from __future__ import annotations
from dataclasses import dataclass
from integration.ground_truth import canonical_plan, bind_step
from integration.contracts import op_contract, schema_hash, dependency

@dataclass
class ValidationResult:
    ok: bool
    reasons: list[str]

def validate_plan(plan, req, contract)->ValidationResult:
    reasons=[]; expected=canonical_plan(req,contract)
    if plan.operation_family!=req['operation_family']: reasons.append('operation_family_mismatch')
    if len(plan.steps)!=len(expected.steps): reasons.append('step_count_mismatch')
    for i,(a,e) in enumerate(zip(plan.steps,expected.steps)):
        if (a.api,a.operation)!=(e.api,e.operation): reasons.append(f'step_{i}_operation_mismatch'); continue
        amap={(m['source'],m['target']) for m in a.parameter_map}; emap={(m['source'],m['target']) for m in e.parameter_map}
        if amap!=emap: reasons.append(f'step_{i}_parameter_map_mismatch')
        if a.auth_scope!=e.auth_scope: reasons.append(f'step_{i}_auth_scope_mismatch')
        if a.api!='agent':
            spec=op_contract(contract,a.api,a.operation)
            payload=bind_step(a,req)['payload']
            missing=[x for x in spec.get('required',[]) if x not in payload]
            if 'approval_code' in spec.get('conditional',{}) and int(payload.get('amount_cents',0))>10000 and not payload.get('approval_code'): missing.append('approval_code')
            if missing: reasons.append(f'step_{i}_missing_required:{sorted(set(missing))}')
    return ValidationResult(not reasons,reasons)

def capability_dependencies(plan)->list[str]: return sorted({dependency(s.api,s.operation) for s in plan.steps if s.api!='agent'})

def validate_capability(cap, req, contract)->ValidationResult:
    reasons=[]
    if cap.validation_status!='validated': reasons.append('not_validated')
    if cap.operation_family!=req['operation_family']: reasons.append('family_mismatch')
    if int(cap.contract_version)!=int(contract['contract_version']):
        # Version mismatch only matters if one of the capability's dependencies changed in the new contract.
        changed=set(contract.get('changed_dependencies',[])); deps=set(cap.dependencies)
        if changed & deps: reasons.append('affected_contract_version_mismatch')
    for s in cap.plan.steps:
        if s.api=='agent': continue
        key=dependency(s.api,s.operation)
        current_req=schema_hash(contract,s.api,s.operation,'request'); current_resp=schema_hash(contract,s.api,s.operation,'response')
        if cap.request_schema_hashes.get(key)!=current_req: reasons.append(f'{key}:request_schema_changed')
        if cap.response_schema_hashes.get(key)!=current_resp: reasons.append(f'{key}:response_schema_changed')
    # Current request-specific validation catches conditionals such as high-value approval codes.
    pv=validate_plan(cap.plan,req,contract); reasons.extend(pv.reasons)
    return ValidationResult(not reasons,sorted(set(reasons)))

def audit_plan(plan, req, contract)->ValidationResult: return validate_plan(plan,req,contract)
