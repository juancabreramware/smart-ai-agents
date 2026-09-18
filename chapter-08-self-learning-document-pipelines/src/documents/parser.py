from __future__ import annotations
from pathlib import Path
from pypdf import PdfReader

def extract_text(path: str|Path)->str:
    reader=PdfReader(str(path))
    return "\n".join((p.extract_text() or "") for p in reader.pages)
