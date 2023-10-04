import pytest

from google.cloud.firestore import Client

from moshi.activ import MinA

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