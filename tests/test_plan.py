import pytest

from google.cloud.firestore import Client
from loguru import logger

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

@pytest.fixture
def live_minpl(minpl: MinPl, db: Client) -> MinPl:
    # covers create and delete
    try:
        minpl.delete(db)
    except Exception as exc:
        logger.error(f"Error deleting minpl: {exc}")
        pass
    minpl.create(db)
    return minpl

def test_minpl(minpl: MinPl):
    assert minpl.uid, "User ID should be set."

@pytest.mark.fb
def test_live_minpl(live_minpl: MinPl, db: Client):
    doc = live_minpl.docref(db).get()
    assert doc.exists
    assert doc.to_dict()['aid'] == live_minpl.aid

@pytest.mark.fb
def test_read_minpl(live_minpl: MinPl, db: Client):
    minpl = live_minpl
    doc = minpl.docref(db).get()
    assert doc.exists
    assert doc.to_dict()['aid'] == minpl.aid
    minpl2 = MinPl.read(minpl.docpath, db)
    assert minpl2 == minpl
