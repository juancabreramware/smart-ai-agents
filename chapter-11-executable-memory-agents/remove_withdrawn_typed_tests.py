from pathlib import Path
for name in ("test_typed_output_contract_v104.py","test_typed_output_contract_v1041.py"):
    p=Path("tests")/name
    if p.exists():
        p.unlink()
        print("Removed withdrawn",name)
