from __future__ import annotations
import math,re
INT=re.compile(r"^[+-]?\d+$")
NUM=re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
VALUE_TYPES={"inventory_reorder":"integer","shipment_sla":"boolean","invoice_escalation":"boolean","supplier_score":"number","customer_action":"boolean","order_priority":"boolean"}
def value_type_for_operation(op):
    if op not in VALUE_TYPES: raise ValueError(f"No value type for {op!r}")
    return VALUE_TYPES[op]
def normalize_typed_value(v,k):
    if k=="boolean":
        if type(v) is not bool: raise ValueError(f"Expected JSON boolean, got {v!r}")
        return v
    if k=="integer":
        if type(v) is bool: raise ValueError(f"Expected integer, got {v!r}")
        if type(v) is int:return v
        if isinstance(v,str) and INT.fullmatch(v.strip()):return int(v.strip())
        raise ValueError(f"Expected integer, got {v!r}")
    if k=="number":
        if type(v) is bool: raise ValueError(f"Expected number, got {v!r}")
        if isinstance(v,(int,float)):n=float(v)
        elif isinstance(v,str) and NUM.fullmatch(v.strip()):n=float(v.strip())
        else:raise ValueError(f"Expected number, got {v!r}")
        if not math.isfinite(n):raise ValueError(f"Expected finite number, got {v!r}")
        return n
    raise ValueError(f"Unsupported kind {k!r}")
def typed_equal(a,b,k,tolerance=1e-9):
    a=normalize_typed_value(a,k);b=normalize_typed_value(b,k)
    return abs(float(a)-float(b))<=tolerance if k=="number" else a==b
