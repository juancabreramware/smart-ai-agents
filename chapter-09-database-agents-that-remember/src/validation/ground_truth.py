from decimal import Decimal
def norm(v):
    if isinstance(v,float): return str(Decimal(str(v)).quantize(Decimal('0.01')))
    if isinstance(v,dict): return {k:norm(x) for k,x in sorted(v.items())}
    if isinstance(v,list): return [norm(x) for x in v]
    return v
def audit(expected,actual,expected_label=None,actual_label=None):
    e,a=norm(expected),norm(actual); ok=e==a and (expected_label is None or expected_label==actual_label)
    return {'ok':ok,'component_accuracy':1.0 if ok else 0.0,'reasons':[] if ok else ['result_or_semantic_mismatch']}
