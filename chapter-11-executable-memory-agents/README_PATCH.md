Chapter 11 v1.0.4.2
Corrected against the actual recovered v1.0.3 provider structure:
payload() -> _public_contract_with_semantics(r).

Changes:
- Adds value_type inside _public_contract_with_semantics().
- Adds explicit model instruction for boolean/integer/number JSON types.
- Strict Boolean validation; 0/1 and strings are not booleans.
- Integer and numeric serialization normalization retained.
- Adds integer llm_call_count evidence field and sums it.
- Validates transformations and compiles candidate files before atomic replacement.
- Backs up provider.py and runner.py first.
- Does not change workload, hidden ground truth, contracts/drift, capability logic, routing, or scoring.

Apply:
python .\remove_withdrawn_typed_tests.py
python .\apply_v1042.py
python -m py_compile .\src\provider.py .\src\typed_values.py .\src\runner.py
python -m pytest -q
