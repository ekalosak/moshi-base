import pytest

from google.cloud.firestore import Client

from moshi import Prompt
from moshi.activ import MinA, UnstrA

def test_mina(mina: MinA):
    assert 1

@pytest.mark.fb
def test_set_mina(mina: MinA, db: Client):
    print(f"Writing to {mina.docpath}")
    mina.set(db)
    doc = mina.docpath.to_docref(db).get()
    assert doc.exists

@pytest.mark.fb
def test_read_mina(mina: MinA, db: Client):
    mina.set(db)
    mina2 = MinA.read(mina.docpath, db)
    assert mina == mina2

@pytest.mark.fb
def test_unstra(bcp47: str, prompt: Prompt, db: Client):
    act = UnstrA(bcp47=bcp47, prompt=prompt)
    act.set(db)
    doc = act.docref(db).get()
    assert doc.exists
    assert UnstrA.read(act.docpath, db) == act