from __future__ import annotations
import math
import re

_NUMERIC = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")

def normalize_numeric(value):
    if isinstance(value, bool):
        raise ValueError(f"Boolean is not numeric: {value!r}")
    if isinstance(value, (int, float)):
        number=value
    elif isinstance(value, str):
        s=value.strip()
        if not _NUMERIC.fullmatch(s):
            raise ValueError(f"Not a strict numeric string: {value!r}")
        number=float(s) if any(ch in s.lower() for ch in (".","e")) else int(s)
    else:
        raise ValueError(f"Unsupported numeric type: {type(value).__name__}")
    if isinstance(number,float) and not math.isfinite(number):
        raise ValueError(f"Non-finite numeric value: {value!r}")
    return number

def numerically_equal(left,right,tolerance=1e-9):
    a=normalize_numeric(left); b=normalize_numeric(right)
    return abs(float(a)-float(b)) <= tolerance
