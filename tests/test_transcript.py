""" Test the live session state. """
import pytest
from google.cloud.firestore import Client

from moshi.transcript import Transcript, Message, Plan, ActT
from moshi.storage import DocPath

@pytest.fixture(params=['live', 'final'])
def status(request) -> str:
    return request.param

@pytest.fixture
def tra(status: str, uid: str, bcp47: str, db: Client) -> Transcript:
    tra = Transcript(
        aid='doesn\'t exist',
        atp=ActT.MIN,
        pid='doesn\'t exist',
        uid=uid,
        bcp47=bcp47,
        status=status,
    )
    try:
        tra.delete(db)
    except Exception as e:
        print(f"Error deleting transcript: {e}")
    return tra

def test_fixture(tra):
    assert tra.status in {'live', 'final'}

def test_create_no_msg(tra: Transcript, db: Client):
    tra.create(db)
    doc = tra.docref(db).get()
    assert doc.exists
    from pprint import pprint; pprint(doc.to_dict())
    print(doc.id)

def test_create_with_msg(tra: Transcript, db: Client):
    tra.messages = [Message('usr', 'hello')]
    tra.create(db)
    doc = tra.docref(db).get()
    assert doc.exists
    from pprint import pprint; pprint(doc.to_dict())
    print(doc.id)

def test_add_msg(tra: Transcript, db):
    tra.create(db)
    msg = Message('usr', 'hello')
    if tra.status == 'final':
        with pytest.raises(ValueError):
            tra.add_msg(msg, db)
    else:
        mid = tra.add_msg(msg, db)
        doc = tra.docref(db).collection('umsgs').document(mid).get()
        dat = doc.to_dict()
        assert Message(**dat) == msg