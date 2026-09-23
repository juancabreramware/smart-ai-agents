from src.capabilities.models import QueryCapability
from src.capabilities.compatibility import compatible
def test_contract_drift_invalidates():
    c=QueryCapability('x',1,'x','V1','SELECT 1',[], 'fp')
    ok,checks=compatible(c,{'query_family':'x','contract_version':'V2','parameters':{}},'fp')
    assert not ok and not checks['contract_version']
