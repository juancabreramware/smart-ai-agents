import re
from .contracts import get_contract
from .capabilities import execute
LABELS={1:"weather",2:"customs",3:"damage",4:"policy_exception"}
def note_label(note):
    if not note:return None
    m=re.search(r"\bnote\s+(\d+)\b",note.lower())
    return "unknown" if not m else LABELS[((int(m.group(1))-1)%4)+1]
def expected(r):
    c=get_contract(r.family,r.contract_version)
    return execute(c.operation,r.inputs,c,note_label(r.note) if r.reasoning_required else None)
