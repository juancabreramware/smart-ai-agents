from __future__ import annotations
from dataclasses import dataclass, field
from copy import deepcopy
from workflows.schema import WorkflowPlan, Step

class ExecutionError(RuntimeError): pass

@dataclass
class EmployeeState:
    identity: bool=False
    mailbox: bool=False
    groups: set[str]=field(default_factory=set)
    source_control: bool=False
    repositories: set[str]=field(default_factory=set)
    project_user: bool=False
    projects: set[str]=field(default_factory=set)
    mfa: bool=False
    security_awareness: bool=False
    crm: bool=False
    disabled: bool=False
    access_expiration: str|None=None
    temp_elevated: bool=False
    notifications: list[str]=field(default_factory=list)
    email: str|None=None

class EnterpriseEnvironment:
    def __init__(self, policy: dict):
        self.policy=deepcopy(policy)
        self.people: dict[str, EmployeeState]={}
        self.ledger=[]

    def snapshot(self):
        return deepcopy(self.people)

    def person(self, employee_id:str)->EmployeeState:
        return self.people.setdefault(employee_id, EmployeeState())


    def seed_for_request(self, request:dict):
        """Prepare deterministic preconditions for workflows that act on an existing employee."""
        f=request["workflow_family"]
        if f.endswith("onboarding"):
            return
        s=self.person(request["employee_id"])
        # Existing-employee workflows start from a realistic active state.
        s.identity=True; s.mailbox=True; s.disabled=False; s.email=request.get("email")
        dept=request.get("department","Engineering")
        s.groups.add(dept)
        s.project_user=True; s.projects.add(request.get("project","ENG"))
        if dept=="Engineering" or f in {"repository_access_change","department_transfer_out_of_engineering"}:
            s.source_control=True
        if f in {"standard_employee_offboarding","immediate_security_offboarding","contractor_expiration","department_transfer_out_of_engineering"}:
            s.repositories.add(request.get("repository","engineering-main"))
        if dept=="Sales": s.crm=True
        if f=="return_from_leave_reactivation":
            s.identity=False; s.mailbox=False; s.disabled=True

    def execute(self, employee_id:str, plan:WorkflowPlan, request:dict)->list[dict]:
        events=[]
        for idx, step in enumerate(plan.steps):
            event=self._apply(employee_id, step, request)
            event["index"]=idx
            events.append(event)
            self.ledger.append(event)
        return events

    def _apply(self, eid:str, step:Step, req:dict)->dict:
        s=self.person(eid); op=step.op; a={**step.args}
        def require(cond,msg):
            if not cond: raise ExecutionError(msg)
        if op=="create_identity":
            s.identity=True; s.disabled=False; s.email=req.get("email")
        elif op=="create_mailbox":
            require(s.identity,"identity required before mailbox"); s.mailbox=True
        elif op=="add_group_member":
            require(s.identity,"identity required before group"); s.groups.add(a["group"])
        elif op=="create_source_control_user":
            require(s.identity,"identity required before source control"); s.source_control=True
        elif op=="require_mfa_enrollment":
            require(s.identity,"identity required before MFA"); s.mfa=True
        elif op=="ack_security_awareness":
            require(s.identity,"identity required before security awareness"); s.security_awareness=True
        elif op=="grant_repository_access":
            require(s.source_control,"source-control account required")
            if self.policy["version"]>=2 and req.get("department")=="Engineering":
                require(s.mfa,"V2 requires MFA before repository access")
            s.repositories.add(a["repository"])
        elif op=="create_project_user":
            require(s.identity,"identity required before project user"); s.project_user=True
        elif op=="add_project_member":
            require(s.project_user,"project user required")
            if self.policy["version"]>=2 and req.get("department")=="Finance":
                require(s.security_awareness,"V2 requires awareness before Finance project/group access")
            s.projects.add(a["project"])
        elif op=="create_crm_user":
            require(s.identity,"identity required before CRM"); s.crm=True
        elif op=="set_access_expiration":
            s.access_expiration=a["date"]
        elif op=="send_notification":
            s.notifications.append(a.get("template","generic"))
        elif op=="revoke_repository_access":
            s.repositories.discard(a["repository"])
        elif op=="disable_source_control_user":
            s.source_control=False; s.repositories.clear()
        elif op=="remove_project_member":
            s.projects.discard(a["project"])
        elif op=="disable_project_user":
            s.project_user=False; s.projects.clear()
        elif op=="disable_crm_user":
            s.crm=False
        elif op=="remove_group_member":
            s.groups.discard(a["group"])
        elif op=="disable_mailbox":
            s.mailbox=False
        elif op=="disable_identity":
            s.disabled=True; s.identity=False
        elif op=="reactivate_identity":
            s.identity=True; s.disabled=False
        elif op=="rename_identity":
            pass
        elif op=="change_email":
            s.email=a["email"]
        elif op=="grant_temporary_elevated_access":
            s.temp_elevated=True
        elif op=="revoke_temporary_elevated_access":
            s.temp_elevated=False
        else:
            raise ExecutionError(f"unsupported op {op}")
        return {"employee_id":eid,"op":op,"args":a,"ok":True}
