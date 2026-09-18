from __future__ import annotations
import hashlib,re

def fingerprint(text:str)->str:
    anchors=[]
    for line in text.splitlines():
        if ':' in line:
            key=line.split(':',1)[0].strip().upper()
            if key and key not in {'EXCEPTION_NOTE'}: anchors.append(key)
    material='|'.join(sorted(set(anchors)))
    return hashlib.sha256(material.encode()).hexdigest()

def compatible(cap, family_id, version, text):
    fp_match=cap.fingerprint==fingerprint(text)
    checks={
      'family':cap.family_id==family_id,
      # An unchanged V2 family remains compatible when its structural fingerprint is identical.
      'contract_version':cap.family_contract_version==version or fp_match,
      'fingerprint':fp_match,
      'validated':cap.validation_status=='validated'}
    return all(checks.values()),checks
