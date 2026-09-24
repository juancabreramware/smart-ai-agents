from src.provider import MockProvider
from src.workload import build
from src.capabilities import promote,compatible,POLICY_HASH
def test_promote_valid_candidate():
    r=build()[0]; pr=MockProvider().reason(r); cap=promote(r,pr); assert cap is not None
def test_promoted_capability_compatible_same_contract():
    r=build()[0]; cap=promote(r,MockProvider().reason(r)); assert compatible(cap,r)
def test_policy_hash_64(): assert len(POLICY_HASH)==64
