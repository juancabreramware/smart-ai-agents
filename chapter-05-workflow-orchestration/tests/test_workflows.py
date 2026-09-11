import json, unittest
from pathlib import Path
from providers.planner import MockPlanner
from environment.simulator import EnterpriseEnvironment, ExecutionError
from workflows.ground_truth import canonical_plan
from smart_agent.validation import validate_plan
from smart_agent.capability_registry import CapabilityRegistry
from smart_agent.agent import SmartWorkflowAgent
from naive_cache.plan_cache import NaivePlanCacheAgent

ROOT=Path(__file__).resolve().parents[1]
P1=json.loads((ROOT/"policies/policy_v1.json").read_text())
P2=json.loads((ROOT/"policies/policy_v2.json").read_text())
def req(f="engineering_employee_onboarding", eid="E1", v=1, **kw):
    x={"request_id":"t","policy_version":v,"workflow_family":f,"employee_id":eid,
       "department":"Engineering","employment_type":"employee","email":"x@n.example",
       "repository":"engineering-main","project":"ENG","group":"Engineering"}
    x.update(kw); return x

class WorkflowTests(unittest.TestCase):
    def test_v1_engineering_has_no_mfa(self):
        ops=[s.op for s in canonical_plan(req(),P1).steps]
        self.assertNotIn("require_mfa_enrollment",ops)

    def test_v2_engineering_has_mfa_before_repo(self):
        ops=[s.op for s in canonical_plan(req(v=2),P2).steps]
        self.assertLess(ops.index("require_mfa_enrollment"),ops.index("grant_repository_access"))

    def test_v2_finance_requires_awareness(self):
        r=req("finance_employee_onboarding",department="Finance",v=2)
        ops=[s.op for s in canonical_plan(r,P2).steps]
        self.assertLess(ops.index("ack_security_awareness"),ops.index("add_group_member"))

    def test_validator_rejects_v1_plan_under_v2(self):
        r=req(v=2); old=canonical_plan(r,P1)
        self.assertFalse(validate_plan(old,r,P2).ok)

    def test_smart_acquires_then_reuses(self):
        reg=CapabilityRegistry(); a=SmartWorkflowAgent(MockPlanner(),reg)
        r1=req(eid="E1"); r2=req(eid="E2")
        self.assertEqual(a.handle(r1,P1,EnterpriseEnvironment(P1))["path"],"INITIAL_ACQUISITION")
        self.assertEqual(a.handle(r2,P1,EnterpriseEnvironment(P1))["path"],"DETERMINISTIC_REUSE")

    def test_selective_invalidation(self):
        reg=CapabilityRegistry(); a=SmartWorkflowAgent(MockPlanner(),reg)
        a.handle(req(eid="E1"),P1,EnterpriseEnvironment(P1))
        sr=req("sales_employee_onboarding","S1",department="Sales",group="Sales")
        a.handle(sr,P1,EnterpriseEnvironment(P1))
        invalidated=reg.invalidate_changed(P2["changed_dependencies"])
        self.assertTrue(any(x.startswith("engineering_employee_onboarding") for x in invalidated))
        self.assertIsNotNone(reg.active("sales_employee_onboarding"))

    def test_relearning_after_policy_change(self):
        reg=CapabilityRegistry(); a=SmartWorkflowAgent(MockPlanner(),reg)
        a.handle(req(eid="E1"),P1,EnterpriseEnvironment(P1))
        reg.invalidate_changed(P2["changed_dependencies"])
        out=a.handle(req(eid="E2",v=2),P2,EnterpriseEnvironment(P2))
        self.assertEqual(out["path"],"RELEARNING")
        self.assertEqual(reg.active("engineering_employee_onboarding").version,2)

    def test_naive_cache_goes_stale(self):
        a=NaivePlanCacheAgent(MockPlanner())
        a.handle(req(eid="E1"),P1,EnterpriseEnvironment(P1))
        out=a.handle(req(eid="E2",v=2),P2,EnterpriseEnvironment(P2))
        self.assertFalse(out["ok"])
        self.assertTrue(out["incorrect_stale_reuse"])

    def test_contractor_has_expiration(self):
        r=req("engineering_contractor_onboarding",employment_type="contractor",end_date="2026-12-31")
        ops=[s.op for s in canonical_plan(r,P1).steps]
        self.assertIn("set_access_expiration",ops)

    def test_workload_is_exactly_150(self):
        xs=json.loads((ROOT/"workloads/full_150.json").read_text())
        self.assertEqual(len(xs),150)
        self.assertEqual(sum(x["policy_version"]==1 for x in xs),100)
        self.assertEqual(sum(x["policy_version"]==2 for x in xs),50)

    def test_reasoning_required_is_not_promoted(self):
        reg=CapabilityRegistry(); a=SmartWorkflowAgent(MockPlanner(),reg)
        r=req("temporary_elevated_access",reuse_allowed=False,request_class="D")
        out=a.handle(r,P1,EnterpriseEnvironment(P1))
        self.assertEqual(out["path"],"REASONING_REQUIRED")
        self.assertIsNone(reg.active("temporary_elevated_access"))

    def test_workload_class_distribution(self):
        xs=json.loads((ROOT/"workloads/full_150.json").read_text())
        self.assertEqual(sum(not x["reuse_allowed"] for x in xs),18)
        self.assertEqual(sum(x["request_class"]=="C" for x in xs),28)

if __name__=="__main__": unittest.main()
