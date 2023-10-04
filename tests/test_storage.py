from google.api_core.exceptions import PermissionDenied
from google.cloud.firestore import Client

from loguru import logger
import pytest

from moshi import __version__
from moshi.storage import FB, DocPath
from moshi.utils import similar

class DummyFb(FB):
    test_key: str = "test_value"
    
    @property
    def docpath(self) -> DocPath:
        dp = DocPath(f'test/{self.test_key}')
        return dp

@pytest.fixture
def fb(db):
    res = DummyFb()
    try:
        res.delete(db)
    except PermissionDenied:
        logger.warning("Permission denied when deleting test doc")
    return res

def test_docpath(db):
    assert DocPath('test_col/test_doc').to_docref(db).id == 'test_doc'

@pytest.mark.fb
def test_fb_fixture(fb: FB, db: Client):
    dr = fb.docref(db)
    assert fb.docref(db).get().exists == False

def test_fb_base_version(fb: DummyFb):
    assert fb.base_version

def test_fb_to_dict(fb: DummyFb):
    expected_dict = {"base_version": fb.base_version, "test_key": "test_value"}
    assert fb.to_dict() == expected_dict

def test_fb_to_jsons(fb: DummyFb):
    expected_jsons = '{"base_version": "' + fb.base_version + '", "test_key": "test_value"}'
    assert similar(fb.to_jsons(), expected_jsons) > 0.99

def test_fb_to_json(fb: DummyFb):
    expected_json = { "base_version": fb.base_version, "test_key": "test_value"}
    assert fb.to_json() == expected_json

@pytest.mark.fb
def test_fb_set(fb: DummyFb, db: Client):
    fb.set(db)
    dsnap = fb.docref(db).get()
    assert dsnap.exists
    assert dsnap.to_dict() == fb.to_dict()

@pytest.mark.fb
def test_fb_read(fb: DummyFb, db: Client):
    fb.set(db)
    fb2 = DummyFb.read(fb.docpath, db)
    assert fb2.to_dict() == fb.to_dict()

@pytest.mark.fb
def test_fb_delete(fb: DummyFb, db: Client):
    fb.set(db)
    fb.delete(db)
    assert fb.docref(db).get().exists == False

@pytest.mark.fb
def test_fb_update(fb: DummyFb, db: Client):
    fb.set(db)
    doc = fb.docref(db).get()
    assert doc.exists, "Failed to write test doc"
    fb.test_key = "updated_value"
    fb.update(db)
    assert fb.docref(db).get().to_dict() == fb.to_dict()