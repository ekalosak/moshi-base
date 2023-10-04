import pytest

from moshi.user import User

@pytest.fixture
def usr():
    return User(uid="test", name="test", language="test", native_language="test")

def test_user(usr: User):
    assert 1

@pytest.mark.fb
def test_user_fb(usr: User, db):
    usr.set(db)
    usr2 = User.read(usr.docpath, db)
    assert usr == usr2
    usr.name = "test2"
    usr.update(db)
    usr3 = User.from_uid(usr.uid, db)  # NOTE to test from_uid; equiv to read
    assert usr3.name == "test2"
    usr.delete(db)
    with pytest.raises(ValueError):
        _ = User.read(usr.docpath, db)
