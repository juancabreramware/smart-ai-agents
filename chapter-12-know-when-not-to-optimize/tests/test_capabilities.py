import pytest
from src.workload import build
from src.capabilities import promote,execute
from src.scoring import ground_truth
def test_capability_executes_trusted_runtime():
    r=next(x for x in build() if x.family=="stable_recurring")
    c=promote(r,"case")
    assert execute(c,r)==ground_truth(r)
def test_incompatible_version_fails():
    rs=[x for x in build() if x.family=="volatile_recurring"]
    a=next(x for x in rs if x.version==1); b=next(x for x in rs if x.version>=2)
    c=promote(a,"case")
    with pytest.raises(ValueError): execute(c,b)
