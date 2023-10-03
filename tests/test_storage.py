import datetime
from google.cloud.firestore import Client

import pytest

from moshi import __version__
from moshi.storage import FB
from moshi.language import similar

class TestFB(FB):
    dummy: str = "test"

    def to_fb(self, db: Client) -> None:
        db.collection("test").document("test").set(self.to_dict())

    @classmethod
    def from_fb(cls, db: Client) -> "TestFB":
        doc = db.collection("test").document("test").get()
        return cls(**doc.to_dict())

@pytest.fixture
def fb():
    return TestFB()

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
