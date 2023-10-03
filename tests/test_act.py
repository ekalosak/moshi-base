import pytest

from moshibase.activ import MinA

@pytest.fixture
def mina():
    return MinA()

def test_mina(mina: MinA):
    assert 1