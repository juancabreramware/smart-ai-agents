from __future__ import annotations
from decimal import Decimal, InvalidOperation

def normalize_scalar(v):
    if isinstance(v,str): return " ".join(v.strip().split())
    return v

def money(v):
    try: return str(Decimal(str(v).replace('$','').replace(',','')).quantize(Decimal('0.01')))
    except InvalidOperation: return str(v)
