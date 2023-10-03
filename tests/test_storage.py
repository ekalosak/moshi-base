import datetime
from google.cloud.firestore import Client

import pytest

from moshi import __version__
from moshi.storage import FB
from moshi.utils import similar

class TestFB(FB):
    docpath: str = "test/test_storage"
    test_key: str = "test_value"

@pytest.fixture
def fb(db):
    res = TestFB()
    res.delete_fb(db)
    return res

def test_fb_fixture(fb: FB, db: Client):
    assert fb.docref(db).get().exists == False

def test_fb_created_at(fb: TestFB):
    assert isinstance(fb.created_at, datetime.datetime)

def test_fb_base_version(fb: TestFB):
    assert fb.base_version

def test_fb_to_dict(fb: TestFB):
    expected_dict = {"created_at": fb.created_at, "base_version": fb.base_version, "dummy": fb.dummy}
    assert fb.to_dict() == expected_dict

def test_fb_to_dict_exclude(fb: TestFB):
    expected_dict = {"base_version": fb.base_version, "dummy": fb.dummy}
    assert fb.to_dict(exclude=["created_at"]) == expected_dict

def test_fb_to_jsons(fb: TestFB):
    expected_jsons = '{"created_at": "%s", "base_version": "%s", "dummy": "test"}' % (fb.created_at.isoformat(), fb.base_version)
    assert similar(fb.to_jsons(), expected_jsons) > 0.99

def test_fb_to_json(fb: TestFB):
    expected_json = {"created_at": fb.created_at.isoformat(), "base_version": fb.base_version, "dummy": fb.dummy}
    assert fb.to_json() == expected_json

def test_fb_to_json_exclude(fb: TestFB):
    expected_json = {"base_version": fb.base_version, "dummy": fb.dummy}
    assert fb.to_json(exclude=["created_at"]) == expected_json

@pytest.mark.fb
def test_fb_to_fb(fb: TestFB, db: Client):
    fb.to_fb(db)
    dsnap = fb.docref(db).get()
    assert dsnap.exists
    assert dsnap.to_dict() == fb.to_json()

@pytest.mark.fb
def test_fb_from_fb(fb: TestFB, db: Client):
    ...