from __future__ import annotations
from integration.schema import ApiStep, IntegrationPlan


def pm(*pairs): return [{'source':a,'target':b} for a,b in pairs]

def canonical_plan(req:dict, contract:dict)->IntegrationPlan:
    f=req['operation_family']; v=int(contract['contract_version']); reusable=bool(req.get('reuse_allowed',True))
    one={
      'crm_lookup_customer': ApiStep('crm','lookup_customer',pm(('customer_id','customer_id')),'',),
    }
    # Construct explicitly to keep the mapping auditable.
    if f=='crm_lookup_customer': steps=[ApiStep('crm','lookup_customer',pm(('customer_id','customer_id')),{},'crm.read')]
    elif f=='crm_update_customer_tag': steps=[ApiStep('crm','update_customer_tag',pm(('customer_id','customer_id'),('tag','tag')),{},'crm.write')]
    elif f=='support_create_ticket':
        pairs=[('customer_id','customer_id'),('subject','subject'),('priority','priority')]
        if v>=2: pairs.append(('category','category'))
        steps=[ApiStep('support','create_ticket',pm(*pairs),{},'support.write')]
    elif f=='support_assign_ticket': steps=[ApiStep('support','assign_ticket',pm(('ticket_id','ticket_id'),('queue','queue')),{},'support.write')]
    elif f=='support_add_comment': steps=[ApiStep('support','add_comment',pm(('ticket_id','ticket_id'),('comment','comment')),{},'support.write')]
    elif f=='billing_get_invoice': steps=[ApiStep('billing','get_invoice',pm(('invoice_id','invoice_id')),{},'billing.read')]
    elif f=='billing_apply_credit':
        pairs=[('customer_id','customer_id'),('reason','reason')]
        if v==1: pairs.insert(1,('amount','amount'))
        else:
            pairs.insert(1,('amount_cents','amount_cents'))
            pairs.append(('approval_code','approval_code'))
        steps=[ApiStep('billing','apply_credit',pm(*pairs),{},'billing.write')]
    elif f=='billing_get_payment_status': steps=[ApiStep('billing','get_payment_status',pm(('invoice_id','invoice_id')),{},'billing.read')]
    elif f=='messaging_send_template': steps=[ApiStep('messaging','send_template',pm(('recipient','recipient'),('template_id','template_id'),('variables','variables')),{},'messaging.send')]
    elif f=='inventory_check_sku': steps=[ApiStep('inventory','check_sku',pm(('sku','sku'),('warehouse_id','warehouse_id')),{},'inventory.read')]
    elif f=='inventory_reserve_sku':
        pairs=[('sku','sku'),('quantity','quantity')]
        if v==1: pairs.insert(1,('warehouse_id','warehouse_id'))
        else:
            pairs.insert(1,('location_id','location_id')); pairs.append(('idempotency_key','idempotency_key'))
        steps=[ApiStep('inventory','reserve_sku',pm(*pairs),{},'inventory.write')]
    elif f=='inventory_release_reservation': steps=[ApiStep('inventory','release_reservation',pm(('reservation_id','reservation_id')),{},'inventory.write')]
    elif f=='identity_lookup_service_user': steps=[ApiStep('identity','lookup_service_user',pm(('user_id','user_id')),{},'identity.read')]
    elif f=='customer_issue_resolution':
        # A simple composition: inspect customer, inspect invoice, then create a support ticket.
        pairs=[('customer_id','customer_id'),('subject','subject'),('priority','priority')]
        if v>=2: pairs.append(('category','category'))
        steps=[ApiStep('crm','lookup_customer',pm(('customer_id','customer_id')),{},'crm.read'),
               ApiStep('billing','get_payment_status',pm(('invoice_id','invoice_id')),{},'billing.read'),
               ApiStep('support','create_ticket',pm(*pairs),{},'support.write')]
    elif f=='exception_credit_request':
        pairs=[('customer_id','customer_id'),('reason','reason')]
        if v==1: pairs.insert(1,('amount','amount'))
        else:
            pairs.insert(1,('amount_cents','amount_cents'))
            pairs.append(('approval_code','approval_code'))
        steps=[ApiStep('billing','apply_credit',pm(*pairs),{},'billing.write')]
    elif f=='ambiguous_customer_action':
        steps=[ApiStep('agent','clarify_request',pm(('clarification','clarification')),{},'')]
    else: raise KeyError(f)
    return IntegrationPlan(f,steps,v,reusable)

def bind_step(step:ApiStep, req:dict)->dict:
    payload=dict(step.constants)
    for m in step.parameter_map:
        if m['source'] in req.get('args',{}): payload[m['target']]=req['args'][m['source']]
    return {'api':step.api,'operation':step.operation,'payload':payload,'auth_scope':step.auth_scope}
