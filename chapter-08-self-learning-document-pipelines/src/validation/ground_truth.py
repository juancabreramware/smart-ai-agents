from __future__ import annotations

def audit(expected:dict, actual:dict, semantic_expected=None, semantic_actual=None):
    total=len(expected)+(1 if semantic_expected is not None else 0); good=0; reasons=[]
    for k,v in expected.items():
        if actual.get(k)==v: good+=1
        else: reasons.append(f'field_mismatch:{k}')
    if semantic_expected is not None:
        if semantic_actual==semantic_expected: good+=1
        else: reasons.append('semantic_label_mismatch')
    return {'ok':good==total,'field_accuracy':good/total if total else 1.0,'reasons':reasons}
