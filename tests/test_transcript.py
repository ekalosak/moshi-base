""" Test the live session state. """
import json

import pytest
from google.cloud.firestore import Client, DocumentSnapshot

from moshi.msg import message
from moshi.transcript import ScoresT, Transcript, ActT
from moshi.grade import Scores, Score, Grade, Level

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

@pytest.mark.fb
def test_fixture(tra):
    assert tra.status in {'live', 'final'}

@pytest.mark.fb
def test_create_no_msg(tra: Transcript, db: Client):
    tra.create(db)
    doc = tra.docref(db).get()
    assert doc.exists
    from pprint import pprint; pprint(doc.to_dict())
    print(doc.id)

@pytest.mark.fb
def test_create_with_msg(tra: Transcript, db: Client):
    tra.add_msg(message('usr', 'hello'))
    tra.create(db)
    doc = tra.docref(db).get()
    assert doc.exists
    from pprint import pprint; pprint(doc.to_dict())
    print(doc.id)
    dat = doc.to_dict()
    assert 'messages' in dat
    assert len(dat['messages']) == 1
    assert dat['messages'].__next__() == 'usr: hello'

@pytest.mark.fb
def test_add_msg(tra: Transcript, db):
    tra.create(db)
    msg = message('usr', 'hello')
    if tra.status == 'final':
        with pytest.raises(ValueError):
            tra.add_msg(msg, db)
    else:
        mid = tra.add_msg(msg, db)
        doc: DocumentSnapshot = tra.docref(db).collection('umsgs').document(mid).get()
        dat = doc.to_dict()
        assert message(**dat) == msg

@pytest.mark.fb
def test_update_msg(tra: Transcript, db):
    tra.create(db)
    msg = message('usr', 'hello')
    if tra.status == 'final':
        with pytest.raises(ValueError):
            mid = tra.add_msg(msg, db, create_in_subcollection=False)
        return
    mid = tra.add_msg(msg, db, create_in_subcollection=False)
    msg.translation = 'bonjour'
    tra.update_msg(msg, mid, db)
    doc = tra.docref(db).get()
    dat = doc.to_dict()
    pld = json.loads(dat['messages'][mid])
    assert message(**pld) == msg

def test_scores_happy():
    tra = Transcript(
        aid='doesn\'t exist',
        atp=ActT.MIN,
        pid='doesn\'t exist',
        uid='doesn\'t exist',
        bcp47='en-MX',
        status='live',
    )
    messages = [
        message('usr', 'hello', score=Scores(vocab=Score(Level.CHILD))),
        message('usr', 'hello', score=Scores(vocab=Score(Level.ERROR), grammar=Score(Level.CHILD))),
        message('usr', 'hello', score=Scores(vocab=Score(Level.ADULT), grammar=Score(Level.CHILD))),
        message('usr', 'hello'),
        message('usr', 'hello', score=Scores(vocab=Score(Level.ADULT), grammar=Score(Level.CHILD))),
    ]
    for msg in messages:
        tra.add_msg(msg)
    scos = tra.scores
    assert isinstance(scos, ScoresT)
    assert scos.vocab.median > Level.CHILD
    assert scos.vocab.median < Level.ADULT
    assert scos.grammar.n == 3

def test_scores_null():
    tra = Transcript(
        aid='doesn\'t exist',
        atp=ActT.MIN,
        pid='doesn\'t exist',
        uid='doesn\'t exist',
        bcp47='en-MX',
        status='live',
    )
    tra.messages = [
        message('usr', 'hello', score=Scores(vocab=Score(Level.CHILD))),
        message('usr', 'hello', score=Scores(vocab=Score(Level.ERROR), grammar=Score(Level.CHILD))),
    ]
    assert not tra.scores

def test_to_templatable_no_messages():
    tra = Transcript(
        aid='test_aid',
        atp=ActT.MIN,
        pid='test_pid',
        uid='test_uid',
        bcp47='en-US',
        tid='test_tid',
        summary='test_summary',
        grade=Grade.ADULT,
        topics=['test_topic1', 'test_topic2'],
        strengths=['test_strength1', 'test_strength2'],
        focus=['test_focus1', 'test_focus2']
    )
    assert tra.to_templatable() == ''

def test_to_templatable_with_messages():
    tra = Transcript(
        aid='test_aid',
        atp=ActT.MIN,
        pid='test_pid',
        uid='test_uid',
        bcp47='en-US',
        tid='test_tid',
        summary='test_summary',
        grade=Grade.EXPERT,
        topics=['test_topic1', 'test_topic2'],
        strengths=['test_strength1', 'test_strength2'],
        focus=['test_focus1', 'test_focus2']
    )
    messages = [
        message('usr', 'hello'),
        message('ast', 'hi'),
    ]
    for msg in messages:
        tra.add_msg(msg)
    assert tra.to_templatable() == 'usr: hello\nast: hi'

def test_to_templatable_with_multiple_messages():
    tra = Transcript(
        aid='test_aid',
        atp=ActT.MIN,
        pid='test_pid',
        uid='test_uid',
        bcp47='en-US',
        tid='test_tid',
        summary='test_summary',
        grade=Grade.BABY,
        topics=['test_topic1', 'test_topic2'],
        strengths=['test_strength1', 'test_strength2'],
        focus=['test_focus1', 'test_focus2']
    )
    for msg in [
            message('usr', 'hello'),
            message('ast', 'hi'),
            message('usr', 'how are you?'),
            message('ast', 'I am doing well, thank you for asking.')
        ]:
        tra.add_msg(msg)
    assert tra.to_templatable() == 'usr: hello\nast: hi\nusr: how are you?\nast: I am doing well, thank you for asking.'
