from pathlib import Path
p=Path("tests/test_typed_output_contract_v104.py")
if p.exists(): p.unlink(); print("Removed withdrawn v1.0.4 test.")
else: print("Withdrawn v1.0.4 test not present.")
