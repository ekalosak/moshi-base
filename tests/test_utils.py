from datetime import datetime

import pytest

from moshi import utils

def test_flatten():
    inp_dict = {"foo": {"bar": 1}}
    exp_out = {"foo.bar": 1}
    assert utils.flatten(inp_dict) == exp_out

def test_random_string():
    rs = utils.random_string(12)
    assert len(rs) == 12

def test_id_prefix():
    _ = utils.id_prefix()

def test_similar():
    assert utils.similar("asdf", "asdF") == 0.75
    assert utils.similar("asdf", "asdf") == 1.
    assert utils.similar("asdf", "qwer") == 0.

def test_jsonify():
    class Zop:
        def __init__(self):
            self.glee = "glop"
        def to_json(self):
            return {"glee": self.glee}
    pld = {
        "foo": "bar",
        "baz": datetime.now(),
        "xip": Zop(),
    }
    assert utils.jsonify(pld) == {
        "foo": "bar",
        "baz": utils._toRFC3339(pld["baz"]),
        "xip": {"glee": "glop"},
    }