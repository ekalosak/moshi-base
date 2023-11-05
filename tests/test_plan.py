import pytest
from google.cloud.firestore import Client
from loguru import logger

from moshi import Message
from moshi.activ import MinA, MinPl, UnstrA, UnstrPl, pid2plan
from moshi.msg import message


@pytest.fixture
def minpl(mina: MinA, uid: str) -> MinPl:
    # Most common method for creating Plan is from Activity. 
    return MinPl.from_act(mina, uid, voice='en-US-Wavenet-A')

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

@pytest.mark.fb
def test_unstrpl(unstra: UnstrA, uid: str):
    upl = UnstrPl.from_act(unstra, uid, voice='en-US-Wavenet-A')
    assert upl.uid, "User ID should be set."

@pytest.fixture
def unstrpl(unstra: UnstrA, uid: str) -> UnstrPl:
    return UnstrPl.from_act(unstra, uid, voice='en-US-Wavenet-A')

@pytest.mark.fb
def test_unstra_reply_wrong_plan_type(unstra: UnstrA, minpl: MinPl, db: Client):
    umsg = message('usr', "Hello!")
    with pytest.raises(TypeError):
        unstra.reply([umsg], minpl)

@pytest.mark.fb
@pytest.mark.openai
def test_unstra_reply(unstra: UnstrA, unstrpl: UnstrPl, db: Client):
    umsg = message('usr', "Hello!")
    amsg = unstra.reply([umsg], unstrpl)
    assert isinstance(amsg, Message)
    assert amsg.role == 'ast'
    assert len(amsg.body) > 5, "Unexpectedly short completion response."

@pytest.mark.fb
def test_pid2plan(minpl: MinPl, db: Client):
    minpl.delete(db)
    minpl.create(db)
    minpl2 = pid2plan(minpl.pid, minpl.uid, db)
    assert minpl2 == minpl