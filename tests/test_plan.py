import pytest

from google.cloud.firestore import Client

from moshi.activ import MinPl, MinA

@pytest.fixture
def uid() -> str:
    return 'test-user'

@pytest.fixture
def bcp47() -> str:
    return 'en-US'

@pytest.fixture
def minpl(mina: MinA, uid: str) -> MinPl:
    # Most common method for creating Plan is from Activity. 
    return MinPl.from_act(mina, uid)

def test_minpl(minpl: MinPl):
    assert 1

def test_minpl_create(db: Client, uid: str, bcp47: str):
    minpl = MinPl(uid, bcp47)