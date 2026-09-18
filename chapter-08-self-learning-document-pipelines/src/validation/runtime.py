from __future__ import annotations
from decimal import Decimal,InvalidOperation

def validate(fields:dict, required:list[str])->dict:
    missing=[k for k in required if fields.get(k) in (None,'',[])]
    checks={'required_fields':not missing,'missing':missing}
    try:
        if {'subtotal','tax','total'} <= fields.keys() and fields.get('fees') is None and fields.get('subtotal') and fields.get('tax') and fields.get('total'):
            checks['arithmetic']=Decimal(str(fields['subtotal']))+Decimal(str(fields['tax']))==Decimal(str(fields['total']))
        elif {'gross_amount','deductions','net_amount'} <= fields.keys() and fields.get('gross_amount') and fields.get('deductions') and fields.get('net_amount'):
            checks['arithmetic']=Decimal(str(fields['gross_amount']))-Decimal(str(fields['deductions']))==Decimal(str(fields['net_amount']))
    except InvalidOperation: checks['arithmetic']=False
    checks['ok']=all(v for k,v in checks.items() if k not in {'missing','ok'})
    return checks
