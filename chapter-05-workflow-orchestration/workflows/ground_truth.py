from __future__ import annotations
from workflows.schema import WorkflowPlan, Step

DEPENDENCIES = {
 "engineering_employee_onboarding":{"engineering.security.mfa_before_repo"},
 "engineering_contractor_onboarding":{"engineering.security.mfa_before_repo","contractor.expiration"},
 "finance_employee_onboarding":{"finance.security.awareness_before_access"},
 "sales_employee_onboarding":{"sales.crm"},
 "operations_employee_onboarding":{"operations.group"},
 "standard_employee_offboarding":{"offboarding.standard"},
 "immediate_security_offboarding":{"offboarding.security"},
 "contractor_expiration":{"contractor.expiration"},
 "department_transfer_into_engineering":{"engineering.security.mfa_before_repo"},
 "department_transfer_out_of_engineering":{"engineering.access"},
 "repository_access_change":{"engineering.repository","engineering.security.mfa_before_repo"},
 "project_access_change":{"project.access"},
 "temporary_elevated_access":{"security.temporary_elevation"},
 "return_from_leave_reactivation":{"identity.reactivation"},
 "new_manager_access_adjustment":{"manager.access"},
 "employee_name_email_change":{"identity.rename"}
}

REASONING_FAMILIES={"temporary_elevated_access","new_manager_access_adjustment"}

def canonical_plan(req:dict, policy:dict)->WorkflowPlan:
    f=req["workflow_family"]; d=req.get("department"); et=req.get("employment_type","employee")
    eid=req["employee_id"]; start=req.get("start_date","2026-09-15")
    S=lambda op,**args: Step(op,args)
    steps=[]
    if f in {"engineering_employee_onboarding","engineering_contractor_onboarding"}:
        steps=[S("create_identity"),S("create_mailbox"),S("add_group_member",group="Engineering"),
               S("create_source_control_user")]
        if policy["version"]>=2: steps += [S("require_mfa_enrollment")]
        steps += [S("grant_repository_access",repository=req.get("repository","engineering-main")),
                  S("create_project_user"),S("add_project_member",project="ENG")]
        if et=="contractor": steps += [S("set_access_expiration",date=req.get("end_date","2026-12-31"))]
        steps += [S("send_notification",template="engineering_onboarding")]
    elif f=="finance_employee_onboarding":
        steps=[S("create_identity"),S("create_mailbox")]
        if policy["version"]>=2: steps += [S("ack_security_awareness")]
        steps += [S("add_group_member",group="Finance"),S("create_project_user"),
                  S("add_project_member",project="FIN"),S("send_notification",template="finance_onboarding")]
    elif f=="sales_employee_onboarding":
        steps=[S("create_identity"),S("create_mailbox"),S("add_group_member",group="Sales"),
               S("create_crm_user"),S("send_notification",template="sales_onboarding")]
    elif f=="operations_employee_onboarding":
        steps=[S("create_identity"),S("create_mailbox"),S("add_group_member",group="Operations"),
               S("create_project_user"),S("add_project_member",project="OPS"),
               S("send_notification",template="operations_onboarding")]
    elif f in {"standard_employee_offboarding","immediate_security_offboarding","contractor_expiration"}:
        steps=[S("revoke_repository_access",repository=req.get("repository","engineering-main")),
               S("disable_source_control_user"),S("remove_project_member",project=req.get("project","ENG")),
               S("disable_project_user"),S("disable_crm_user"),
               S("remove_group_member",group=req.get("group",d or "Engineering")),
               S("send_notification",template="offboarding_confirmation"),
               S("disable_mailbox"),S("disable_identity")]
    elif f=="department_transfer_into_engineering":
        steps=[S("add_group_member",group="Engineering"),S("create_source_control_user")]
        if policy["version"]>=2: steps += [S("require_mfa_enrollment")]
        steps += [S("grant_repository_access",repository="engineering-main"),
                  S("create_project_user"),S("add_project_member",project="ENG")]
    elif f=="department_transfer_out_of_engineering":
        steps=[S("revoke_repository_access",repository="engineering-main"),S("disable_source_control_user"),
               S("remove_project_member",project="ENG"),S("remove_group_member",group="Engineering"),
               S("add_group_member",group=req.get("new_department","Operations"))]
    elif f=="repository_access_change":
        steps=[]
        if policy["version"]>=2 and req.get("department")=="Engineering": steps += [S("require_mfa_enrollment")]
        steps += [S("grant_repository_access",repository=req.get("repository","engineering-main"))]
    elif f=="project_access_change":
        steps=[S("create_project_user"),S("add_project_member",project=req.get("project","OPS"))]
    elif f=="temporary_elevated_access":
        steps=[S("grant_temporary_elevated_access"),S("send_notification",template="temporary_access")]
    elif f=="return_from_leave_reactivation":
        steps=[S("reactivate_identity"),S("create_mailbox"),S("send_notification",template="return_from_leave")]
    elif f=="new_manager_access_adjustment":
        steps=[S("create_project_user"),S("add_project_member",project=req.get("project","MANAGERS"))]
    elif f=="employee_name_email_change":
        steps=[S("rename_identity"),S("change_email",email=req["email"]),S("send_notification",template="identity_changed")]
    else:
        raise KeyError(f"unknown family {f}")
    return WorkflowPlan(f,steps,"canonical ground truth")

def expected_ops(req:dict, policy:dict):
    return [s.op for s in canonical_plan(req,policy).steps]
