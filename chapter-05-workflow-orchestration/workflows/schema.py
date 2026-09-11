from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

ALLOWED_OPS = {
    "create_identity","create_mailbox","add_group_member","create_source_control_user",
    "grant_repository_access","create_project_user","add_project_member",
    "require_mfa_enrollment","ack_security_awareness","create_crm_user",
    "disable_identity","disable_mailbox","remove_group_member","revoke_repository_access",
    "disable_source_control_user","remove_project_member","disable_project_user",
    "disable_crm_user","set_access_expiration","send_notification","reactivate_identity",
    "rename_identity","change_email","grant_temporary_elevated_access","revoke_temporary_elevated_access"
}

@dataclass(frozen=True)
class Step:
    op: str
    args: dict[str, Any]

@dataclass
class WorkflowPlan:
    workflow_family: str
    steps: list[Step]
    rationale: str = ""

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "WorkflowPlan":
        return cls(
            workflow_family=str(value["workflow_family"]),
            steps=[Step(str(s["op"]), {k:v for k,v in dict(s.get("args", {})).items() if v is not None}) for s in value["steps"]],
            rationale=str(value.get("rationale", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"workflow_family": self.workflow_family,
                "steps": [asdict(s) for s in self.steps],
                "rationale": self.rationale}

PLAN_JSON_SCHEMA = {
    "type":"object",
    "properties":{
        "workflow_family":{"type":"string"},
        "steps":{
            "type":"array","minItems":1,
            "items":{"type":"object","properties":{
                "op":{"type":"string","enum":sorted(ALLOWED_OPS)},
                "args":{"type":"object","properties":{
                    "group":{"type":["string","null"]},
                    "repository":{"type":["string","null"]},
                    "project":{"type":["string","null"]},
                    "date":{"type":["string","null"]},
                    "template":{"type":["string","null"]},
                    "email":{"type":["string","null"]}
                },"required":["group","repository","project","date","template","email"],"additionalProperties":False}
            },"required":["op","args"],"additionalProperties":False}
        },
        "rationale":{"type":"string"}
    },
    "required":["workflow_family","steps","rationale"],
    "additionalProperties":False
}
