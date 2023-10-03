import pytest

from moshi.activ import MinA

@pytest.fixture
def mina():
    return MinA()

def test_mina(mina: MinA):
    assert 1