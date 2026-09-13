from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from integration.contracts import op_contract

class ApiError(RuntimeError): pass

@dataclass
class SimulatorState:
    tags: dict[str,set[str]]=field(default_factory=dict)
    tickets: dict[str,dict]=field(default_factory=dict)
    credits: dict[str,dict]=field(default_factory=dict)
    reservations: dict[str,dict]=field(default_factory=dict)
    idempotency: dict[str,str]=field(default_factory=dict)
    messages: dict[str,dict]=field(default_factory=dict)

class EnterpriseApiSimulator:
    def __init__(self):
        self.state=SimulatorState(); self.api_calls=0; self.seq={'T':1000,'C':2000,'R':3000,'M':4000}
        self.customers={f'CUST-{i:03d}':{'customer_id':f'CUST-{i:03d}','name':f'Customer {i}','status':'active','tags':[]} for i in range(1,80)}
        self.invoices={f'INV-{i:04d}':{'invoice_id':f'INV-{i:04d}','customer_id':f'CUST-{((i-1)%50)+1:03d}','amount_cents':5000+i*7,'status':'paid' if i%3 else 'open'} for i in range(1,200)}
        self.inventory={(sku,wh):10000 for sku in ['SKU-1','SKU-2','SKU-3','SKU-4'] for wh in ['WH-1','WH-2']}
    def _id(self,p): self.seq[p]+=1; return f'{p}-{self.seq[p]}'
    def _validate(self, api, op, payload, contract):
        if api=='agent': return
        spec=op_contract(contract,api,op)
        missing=[x for x in spec.get('required',[]) if x not in payload or payload[x] in (None,'')]
        cond=spec.get('conditional',{})
        if 'approval_code' in cond and int(payload.get('amount_cents',0))>10000 and not payload.get('approval_code'): missing.append('approval_code')
        if missing: raise ApiError(f'{api}.{op} missing required: {missing}')
    def execute(self, action:dict, contract:dict)->dict:
        self.api_calls+=1; api,op,p=action['api'],action['operation'],action['payload']
        self._validate(api,op,p,contract)
        if api=='agent' and op=='clarify_request': return {'clarification':p.get('clarification','Please clarify the requested action.'),'status':'clarification_required'}
        if api=='crm' and op=='lookup_customer': return dict(self.customers[p['customer_id']])
        if api=='crm' and op=='update_customer_tag':
            c=self.customers[p['customer_id']]; tags=set(c['tags']); tags.add(p['tag']); c['tags']=sorted(tags); return {'customer_id':p['customer_id'],'tags':c['tags']}
        if api=='support' and op=='create_ticket':
            tid=self._id('T'); self.state.tickets[tid]=dict(p, ticket_id=tid,status='open'); return {'ticket_id':tid,'status':'open'}
        if api=='support' and op=='assign_ticket':
            t=self.state.tickets.setdefault(p['ticket_id'],{'ticket_id':p['ticket_id'],'status':'open'}); t['queue']=p['queue']; return {'ticket_id':p['ticket_id'],'queue':p['queue']}
        if api=='support' and op=='add_comment':
            t=self.state.tickets.setdefault(p['ticket_id'],{'ticket_id':p['ticket_id'],'status':'open','comments':[]}); t.setdefault('comments',[]).append(p['comment']); return {'ticket_id':p['ticket_id'],'comment_count':len(t['comments'])}
        if api=='billing' and op=='get_invoice': return dict(self.invoices[p['invoice_id']])
        if api=='billing' and op=='get_payment_status':
            x=self.invoices[p['invoice_id']]; return {'invoice_id':p['invoice_id'],'status':x['status']}
        if api=='billing' and op=='apply_credit':
            cid=self._id('C'); self.state.credits[cid]=dict(p,credit_id=cid,status='approved'); return {'credit_id':cid,'status':'approved'}
        if api=='messaging' and op=='send_template':
            mid=self._id('M'); self.state.messages[mid]=dict(p,message_id=mid,status='sent'); return {'message_id':mid,'status':'sent'}
        if api=='inventory' and op=='check_sku':
            wh=p['warehouse_id']; return {'sku':p['sku'],'warehouse_id':wh,'available':self.inventory.get((p['sku'],wh),0)}
        if api=='inventory' and op=='reserve_sku':
            version=int(contract['contract_version']); loc=p['warehouse_id'] if version==1 else p['location_id']
            if version>=2:
                key=p['idempotency_key']
                if key in self.state.idempotency:
                    rid=self.state.idempotency[key]; return {'reservation_id':rid,'status':'reserved','idempotent_replay':True}
            qty=int(p['quantity']); avail=self.inventory.get((p['sku'],loc),0)
            if qty>avail: raise ApiError('insufficient_inventory')
            self.inventory[(p['sku'],loc)]=avail-qty; rid=self._id('R'); self.state.reservations[rid]={'reservation_id':rid,'sku':p['sku'],'location':loc,'quantity':qty,'status':'reserved'}
            if version>=2: self.state.idempotency[p['idempotency_key']]=rid
            return {'reservation_id':rid,'status':'reserved'}
        if api=='inventory' and op=='release_reservation':
            r=self.state.reservations.get(p['reservation_id']);
            if r: r['status']='released'
            return {'reservation_id':p['reservation_id'],'status':'released'}
        if api=='identity' and op=='lookup_service_user': return {'user_id':p['user_id'],'active':True,'scopes':['crm.read','support.write','billing.read','billing.write','messaging.send','inventory.read','inventory.write']}
        raise ApiError(f'unsupported operation {api}.{op}')
