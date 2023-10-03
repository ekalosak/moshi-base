import datetime
from google.cloud.firestore import Client

import pytest

from moshi import __version__
from moshi.storage import FB
from moshi.utils import similar

class DummyFb(FB):
    test_key: str = "test_value"

@pytest.fixture
def fb(db):
    res = DummyFb(docpath="test/test_storage")
    res.delete_fb(db)
    return res

def test_fb_fixture(fb: FB, db: Client):
    assert fb.docref(db).get().exists == False

def test_fb_base_version(fb: DummyFb):
    assert fb.base_version

def test_fb_to_dict(fb: DummyFb):
    expected_dict = {"base_version": fb.base_version, "test_key": "test_value"}
    assert fb.to_dict() == expected_dict

def test_fb_to_jsons(fb: DummyFb):
    expected_jsons = '{"base_version": "%s", "test_key": "test_value"}' % (fb.created_at.isoformat(), fb.base_version)
    assert similar(fb.to_jsons(), expected_jsons) > 0.99

def test_fb_to_json(fb: DummyFb):
    expected_json = { "base_version": fb.base_version, "test_key": "test_value"}
    assert fb.to_json() == expected_json

@pytest.mark.fb
def test_fb_to_fb(fb: DummyFb, db: Client):
    fb.to_fb(db)
    dsnap = fb.docref(db).get()
    assert dsnap.exists
    assert dsnap.to_dict() == fb.to_dict()

@pytest.mark.fb
def test_fb_from_fb(fb: DummyFb, db: Client):
    ...