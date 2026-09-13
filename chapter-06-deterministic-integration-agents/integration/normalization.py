from __future__ import annotations
import re
from integration.schema import ApiStep, IntegrationPlan
from integration.contracts import op_contract

_PREFIXES=("request.args.", "args.")
_BRACKET_RE=re.compile(r"^(?:request\.)?args\[['\"]([^'\"]+)['\"]\]$")


def normalize_source_name(source: str) -> str:
    """Normalize semantically equivalent request argument references to a bare args key."""
    s=str(source).strip()
    for prefix in _PREFIXES:
        if s.startswith(prefix):
            return s[len(prefix):]
    m=_BRACKET_RE.match(s)
    return m.group(1) if m else s


def _normalize_step(step: ApiStep) -> ApiStep:
    seen=set(); mappings=[]
    for item in step.parameter_map:
        source=normalize_source_name(item.get('source',''))
        target=str(item.get('target','')).strip()
        key=(source,target)
        if key in seen:
            continue
        seen.add(key)
        mappings.append({'source':source,'target':target})
    auth_scope=str(step.auth_scope).strip()
    # The benchmark's local clarification action has no external authorization boundary.
    # GPT-5.6 may express that same meaning as the string 'none'. Canonicalize only this
    # exact agent action; never normalize auth scopes for real API operations.
    if step.api=='agent' and step.operation=='clarify_request' and auth_scope.lower()=='none':
        auth_scope=''
    return ApiStep(step.api, step.operation, mappings, dict(step.constants), auth_scope)


def canonicalize_plan(plan: IntegrationPlan, req: dict, contract: dict) -> IntegrationPlan:
    """Canonicalize safe representational variants before strict validation.

    This function intentionally does not repair wrong API choices, wrong operations, missing
    required fields, or wrong auth scopes. It only normalizes equivalent request references,
    completes documented conditional identity mappings for reusable capabilities, and converts
    an explicit no-action response for the benchmark's ambiguity family into its canonical
    clarification action.
    """
    steps=[_normalize_step(s) for s in plan.steps]

    # A model can correctly refuse to call a business API for the explicitly ambiguous family
    # by returning no steps. Keep the ledger uniform by canonicalizing that representation to
    # the benchmark's agent.clarify_request action.
    if plan.operation_family=='ambiguous_customer_action' and not steps and not plan.reusable:
        if 'clarification' in req.get('args',{}):
            steps=[ApiStep('agent','clarify_request',
                           [{'source':'clarification','target':'clarification'}],{},'')]

    # Reusable capabilities must retain documented conditional inputs so a capability acquired
    # on a low-value request remains safe when a later request crosses the condition threshold.
    # We only add a same-name mapping for fields explicitly declared conditional by the active
    # contract and already present in request.args; required fields are never auto-repaired.
    if plan.reusable:
        normalized=[]
        for step in steps:
            if step.api=='agent':
                normalized.append(step); continue
            spec=op_contract(contract,step.api,step.operation)
            targets={m['target'] for m in step.parameter_map}
            mappings=list(step.parameter_map)
            for field in spec.get('conditional',{}):
                if field not in targets and field in req.get('args',{}):
                    mappings.append({'source':field,'target':field})
            normalized.append(ApiStep(step.api,step.operation,mappings,dict(step.constants),step.auth_scope))
        steps=normalized

    return IntegrationPlan(plan.operation_family, steps, int(plan.contract_version), bool(plan.reusable))
