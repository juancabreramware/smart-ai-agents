from pathlib import Path
p=Path("src/provider.py")
s=p.read_text(encoding="utf-8")
anchor="from .models import Candidate,ProviderResult,Usage\n"
imp="from .numeric_normalization import numerically_equal\n"
if imp not in s:
    if anchor not in s: raise SystemExit("Expected v1.0.2 import anchor not found.")
    s=s.replace(anchor,anchor+imp,1)

old='''    mv=o["value"]; cv=canonical.value
    same=(abs(float(mv)-float(cv))<1e-9) if isinstance(mv,(int,float)) and isinstance(cv,(int,float)) else mv==cv
    if not same:
        raise ValueError(f"Provider value conflicts with public contract: model={mv!r}, canonical={cv!r}, raw={o!r}")
'''
new='''    mv=o["value"]; cv=canonical.value
    try:
        same=numerically_equal(mv,cv)
    except ValueError as exc:
        raise ValueError(f"Provider value is not a valid numeric value: model={mv!r}, canonical={cv!r}, raw={o!r}") from exc
    if not same:
        raise ValueError(f"Provider value conflicts with public contract: model={mv!r}, canonical={cv!r}, raw={o!r}")
'''
if old in s:
    s=s.replace(old,new,1)
elif "same=numerically_equal(mv,cv)" not in s:
    raise SystemExit("Expected v1.0.2 comparison block not found.")
p.write_text(s,encoding="utf-8",newline="\n")
print("v1.0.3 applied.")
