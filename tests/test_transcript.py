""" Test the live session state. """
import pytest
from google.cloud.firestore import Client

from moshi.transcript import Transcript, Message, Plan
from moshi.storage import DocPath

@pytest.fixture(params=['live', 'final'])
def status(status: str) -> str:
    return status

@pytest.fixture
def tra(mplan: MinPl, status: str, db: Client) -> Transcript:
    ...

def test_add_msg(transcript, db):
    msg = Message(role='usr', text='hello')
    transcript.add_msg(msg, db)
    assert len(transcript.messages) == 1
    assert transcript.messages[0].text == 'hello'

def test_read(transcript, db):
    docpath = DocPath('users/uid/live/tid')
    db.document.return_value.get.return_value.exists = True
    db.document.return_value.get.return_value.to_dict.return_value = {
        'aid': 'aid',
        'atp': 'atp',
        'pid': 'pid',
        'uid': 'uid',
        'bcp47': 'en-US',
        'status': 'live',
    }
    transcript.read(docpath, db)
    assert transcript.aid == 'aid'
    assert transcript.atp == 'atp'
    assert transcript.pid == 'pid'
    assert transcript.uid == 'uid'
    assert transcript.bcp47 == 'en-US'
    assert transcript.status == 'live'

def test_create(transcript, db):
    transcript.create(db)
    db.document.assert_called_once_with(transcript.docpath)
    db.document.return_value.create.assert_called_once_with(transcript.to_json())

def test_delete(transcript, db):
    transcript.delete(db)
    db.document.assert_called_once_with(transcript.docpath)
    db.document.return_value.delete.assert_called_once_with()