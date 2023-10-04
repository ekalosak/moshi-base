from datetime import datetime

from moshi import utils


def test_flatten():
    inp_dict = {"foo": {"bar": 1}}
    exp_out = {"foo.bar": 1}
    assert utils.flatten(inp_dict) == exp_out

def test_random_string():
    assert len(utils.random_string(12)) == 12

def test_id_prefix():
    _ = utils.id_prefix()

def test_similar():
    assert utils.similar("asdf", "asdF") == 0.75
    assert utils.similar("asdf", "asdf") == 1.
    assert utils.similar("asdf", "qwer") == 0.

def test_jsonify():
    pld = {
        "foo": "bar",
        "baz": datetime.now(),
    }
    assert utils.jsonify(pld) == {
        "foo": "bar",
        "baz": utils._toRFC3339(pld["baz"]),
    }