from src.workload import build
from src.contracts import ALLOWED_OPERATIONS,OPERATION_BY_FAMILY,contract_manifest,contract_hash
from src.runtime import execute,validate_typed
from src.scoring import ground_truth
from src.models import Answer
def test_operation_allowlist_exact(): assert len(ALLOWED_OPERATIONS)==8
def test_contract_manifest_hash_deterministic(): assert contract_hash()==contract_hash() and len(contract_hash())==64
def test_runtime_matches_ground_truth():
    for r in build():
        assert execute(OPERATION_BY_FAMILY[r.family],r)==ground_truth(r)
def test_bool_validation(): assert validate_typed(Answer(True)) and not validate_typed(Answer(1))
