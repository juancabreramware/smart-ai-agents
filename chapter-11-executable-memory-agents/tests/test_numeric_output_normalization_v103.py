import pytest
from src.numeric_normalization import normalize_numeric,numerically_equal

@pytest.mark.parametrize("raw,expected",[("0",0),("50",50),("12.5",12.5),("-3.25",-3.25),("1e3",1000.0),(0,0),(12.5,12.5)])
def test_normalize(raw,expected): assert normalize_numeric(raw)==expected

@pytest.mark.parametrize("raw",["abc","$50","50 units","","NaN","Infinity",True,None])
def test_reject(raw):
    with pytest.raises(ValueError): normalize_numeric(raw)

def test_equivalent_numeric_strings():
    assert numerically_equal("0",0)
    assert numerically_equal("50",50)
    assert numerically_equal("12.5",12.5)

def test_real_difference_rejected():
    assert not numerically_equal("51",50)
