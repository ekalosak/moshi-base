""" Test the live session state. """
import pytest
from google.cloud.firestore import Client

from moshi.transcript import Transcript, Message, Plan, ActT
from moshi.storage import DocPath

@pytest.fixture(params=['live', 'final'])
def status(request) -> str:
    return request.param

@pytest.fixture
def tra(status: str, uid: str, bcp47: str) -> Transcript:
    return Transcript(
        aid='aid',
        atp=ActT.MIN,
        pid='pid',
        uid=uid,
        bcp47=bcp47,
        status=status,
    )

def test_tra_fixture(tra):
    assert tra.status in {'live', 'final'}

# def test_add_msg(tra: Transcript, db):
#     msg = Message('usr', 'hello')
#     if tra.status == 'final':
#         with pytest.raises(ValueError):
#             tra.add_msg(msg, db)
#     else:
#         mid = tra.add_msg(msg, db)
#         doc = tra.docref(db).collection('umsgs').document(mid)
#         dat = doc.get().to_dict()
#         assert Message(**dat) == msg