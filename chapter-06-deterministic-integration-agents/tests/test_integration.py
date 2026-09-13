import json,tempfile,unittest
from pathlib import Path
from integration.contracts import load_contract
from integration.ground_truth import canonical_plan
from integration.normalization import canonicalize_plan, normalize_source_name
from integration.schema import ApiStep, IntegrationPlan
from smart_agent.validation import validate_plan,validate_capability
from smart_agent.capability_registry import CapabilityRegistry
from smart_agent.agent import SmartIntegrationAgent
from naive_cache.agent import NaiveIntegrationCache
from providers.planner import MockPlanner
from environment.simulator import EnterpriseApiSimulator
ROOT=Path(__file__).resolve().parents[1]

def R(f,v=1,i=1,reuse=True):
    args={'customer_id':'CUST-001','subject':'Issue','priority':'high','category':'billing','amount':50,'amount_cents':15000,'reason':'service recovery','approval_code':'APR-1','sku':'SKU-1','warehouse_id':'WH-1','location_id':'WH-1','quantity':1,'idempotency_key':'idem-1','recipient':'x@example.com','template_id':'shipment-delay','variables':{},'invoice_id':'INV-0001','user_id':'U-001','tag':'priority-review','ticket_id':'T-1','queue':'enterprise','comment':'note','reservation_id':'R-1','clarification':'clarify'}
    return {'request_id':f'q{i:03d}','phase':f'V{v}','contract_version':v,'request_class':'A','operation_family':f,'args':args,'reuse_allowed':reuse}

class Tests(unittest.TestCase):
    def test_v1_support_valid(self): self.assertTrue(validate_plan(canonical_plan(R('support_create_ticket'),load_contract(1)),R('support_create_ticket'),load_contract(1)).ok)
    def test_v2_support_rejects_v1(self): self.assertFalse(validate_plan(canonical_plan(R('support_create_ticket'),load_contract(1)),R('support_create_ticket',2),load_contract(2)).ok)
    def test_v2_support_has_category(self): self.assertTrue(validate_plan(canonical_plan(R('support_create_ticket',2),load_contract(2)),R('support_create_ticket',2),load_contract(2)).ok)
    def test_v2_billing_rejects_v1(self): self.assertFalse(validate_plan(canonical_plan(R('billing_apply_credit'),load_contract(1)),R('billing_apply_credit',2),load_contract(2)).ok)
    def test_v2_billing_requires_approval(self):
        req=R('billing_apply_credit',2); req['args'].pop('approval_code'); self.assertFalse(validate_plan(canonical_plan(req,load_contract(2)),req,load_contract(2)).ok)
    def test_v2_inventory_rejects_v1(self): self.assertFalse(validate_plan(canonical_plan(R('inventory_reserve_sku'),load_contract(1)),R('inventory_reserve_sku',2),load_contract(2)).ok)
    def test_unchanged_messaging_survives(self):
        reg=CapabilityRegistry(); cap=reg.promote(canonical_plan(R('messaging_send_template'),load_contract(1)),load_contract(1)); reg.invalidate_for_changes(load_contract(2)['changed_dependencies']); self.assertTrue(validate_capability(cap,R('messaging_send_template',2),load_contract(2)).ok)
    def test_selective_invalidation(self):
        reg=CapabilityRegistry(); a=reg.promote(canonical_plan(R('support_create_ticket'),load_contract(1)),load_contract(1)); b=reg.promote(canonical_plan(R('crm_lookup_customer'),load_contract(1)),load_contract(1)); reg.invalidate_for_changes(load_contract(2)['changed_dependencies']); self.assertEqual(a.validation_status,'invalid'); self.assertEqual(b.validation_status,'validated')
    def test_reasoning_not_promoted(self):
        reg=CapabilityRegistry(); agent=SmartIntegrationAgent(MockPlanner(),reg); agent.handle(R('exception_credit_request',1,reuse=False),load_contract(1),EnterpriseApiSimulator()); self.assertFalse(reg.items)
    def test_smart_acquire_then_reuse(self):
        reg=CapabilityRegistry(); agent=SmartIntegrationAgent(MockPlanner(),reg); env=EnterpriseApiSimulator(); r1=agent.handle(R('crm_lookup_customer'),load_contract(1),env); r2=agent.handle(R('crm_lookup_customer',1,2),load_contract(1),env); self.assertEqual(r1['llm_calls'],1); self.assertEqual(r2['llm_calls'],0); self.assertEqual(r2['path'],'DETERMINISTIC_REUSE')
    def test_repair_promotes_new_version(self):
        reg=CapabilityRegistry(); agent=SmartIntegrationAgent(MockPlanner(),reg); env=EnterpriseApiSimulator(); agent.handle(R('support_create_ticket'),load_contract(1),env); agent.on_contract_change(load_contract(2)); r=agent.handle(R('support_create_ticket',2,2),load_contract(2),env); self.assertEqual(r['path'],'RELEARNING'); self.assertTrue(any(x.version==2 for x in reg.items.values()))
    def test_naive_stale_v2(self):
        agent=NaiveIntegrationCache(MockPlanner()); env=EnterpriseApiSimulator(); agent.handle(R('support_create_ticket'),load_contract(1),env); r=agent.handle(R('support_create_ticket',2,2),load_contract(2),env); self.assertFalse(r['audited_correct']); self.assertTrue(r['incorrect_stale_reuse'])
    def test_idempotency(self):
        req=R('inventory_reserve_sku',2); p=canonical_plan(req,load_contract(2)); from integration.execution import execute_plan; env=EnterpriseApiSimulator(); a=execute_plan(p,req,load_contract(2),env); b=execute_plan(p,req,load_contract(2),env); self.assertEqual(a['final']['reservation_id'],b['final']['reservation_id'])
    def test_workload_exact(self):
        xs=json.loads((ROOT/'workloads/full_150.json').read_text()); self.assertEqual(len(xs),150); self.assertEqual(sum(x['phase']=='V1' for x in xs),100); self.assertEqual(sum(x['phase']=='V2' for x in xs),50)
    def test_distribution(self):
        xs=json.loads((ROOT/'workloads/full_150.json').read_text()); v1=[x for x in xs if x['phase']=='V1']; v2=[x for x in xs if x['phase']=='V2']; self.assertEqual(sum(x['request_class'] in ['A','B'] for x in v1),68); self.assertEqual(sum(x['request_class']=='C' for x in v1),20); self.assertEqual(sum(x['request_class']=='D' for x in v1),12); self.assertEqual(sum(x['request_class']=='D' for x in v2),6)

    def test_normalizes_qualified_request_arg_sources(self):
        req=R('billing_apply_credit',1); contract=load_contract(1)
        plan=IntegrationPlan('billing_apply_credit',[ApiStep('billing','apply_credit',[
            {'source':'request.args.customer_id','target':'customer_id'},
            {'source':'request.args.amount','target':'amount'},
            {'source':'request.args.reason','target':'reason'}],{},'billing.write')],1,True)
        fixed=canonicalize_plan(plan,req,contract)
        self.assertTrue(validate_plan(fixed,req,contract).ok)
        self.assertEqual([m['source'] for m in fixed.steps[0].parameter_map],['customer_id','amount','reason'])

    def test_normalizes_bracket_request_arg_source(self):
        self.assertEqual(normalize_source_name('request.args["customer_id"]'),'customer_id')
        self.assertEqual(normalize_source_name("args['amount']"),'amount')

    def test_ambiguous_empty_plan_becomes_clarification(self):
        req=R('ambiguous_customer_action',1,reuse=False); contract=load_contract(1)
        plan=IntegrationPlan('ambiguous_customer_action',[],1,False)
        fixed=canonicalize_plan(plan,req,contract)
        self.assertTrue(validate_plan(fixed,req,contract).ok)
        self.assertEqual((fixed.steps[0].api,fixed.steps[0].operation),('agent','clarify_request'))

    def test_reusable_v2_credit_completes_conditional_mapping(self):
        req=R('billing_apply_credit',2); req['args']['amount_cents']=7500; contract=load_contract(2)
        plan=IntegrationPlan('billing_apply_credit',[ApiStep('billing','apply_credit',[
            {'source':'customer_id','target':'customer_id'},
            {'source':'amount_cents','target':'amount_cents'},
            {'source':'reason','target':'reason'}],{},'billing.write')],2,True)
        fixed=canonicalize_plan(plan,req,contract)
        self.assertIn({'source':'approval_code','target':'approval_code'},fixed.steps[0].parameter_map)
        self.assertTrue(validate_plan(fixed,req,contract).ok)

    def test_normalizer_does_not_repair_missing_required_mapping(self):
        req=R('support_create_ticket',2); contract=load_contract(2)
        plan=IntegrationPlan('support_create_ticket',[ApiStep('support','create_ticket',[
            {'source':'customer_id','target':'customer_id'},
            {'source':'subject','target':'subject'},
            {'source':'priority','target':'priority'}],{},'support.write')],2,True)
        fixed=canonicalize_plan(plan,req,contract)
        self.assertFalse(validate_plan(fixed,req,contract).ok)
        self.assertTrue(any('category' in x for x in validate_plan(fixed,req,contract).reasons))


    def test_clarification_none_auth_scope_normalizes_to_empty(self):
        req=R('ambiguous_customer_action',1,reuse=False); contract=load_contract(1)
        plan=IntegrationPlan('ambiguous_customer_action',[ApiStep('agent','clarify_request',[
            {'source':'clarification','target':'clarification'}],{},'none')],1,False)
        fixed=canonicalize_plan(plan,req,contract)
        self.assertEqual(fixed.steps[0].auth_scope,'')
        self.assertTrue(validate_plan(fixed,req,contract).ok)

    def test_none_auth_scope_is_not_normalized_for_business_api(self):
        req=R('billing_apply_credit',1); contract=load_contract(1)
        plan=IntegrationPlan('billing_apply_credit',[ApiStep('billing','apply_credit',[
            {'source':'customer_id','target':'customer_id'},
            {'source':'amount','target':'amount'},
            {'source':'reason','target':'reason'}],{},'none')],1,True)
        fixed=canonicalize_plan(plan,req,contract)
        self.assertEqual(fixed.steps[0].auth_scope,'none')
        self.assertFalse(validate_plan(fixed,req,contract).ok)
        self.assertIn('step_0_auth_scope_mismatch',validate_plan(fixed,req,contract).reasons)

    def test_catalog_covers_workload(self):
        catalog=json.loads((ROOT/'catalog/operation_catalog.json').read_text()); xs=json.loads((ROOT/'workloads/full_150.json').read_text()); self.assertTrue({x['operation_family'] for x in xs}.issubset(catalog.keys()))

if __name__=='__main__': unittest.main()
