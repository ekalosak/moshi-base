from moshi.utils import flatten


def test_flatten():
    inp_dict = {"foo": {"bar": 1}}
    exp_out = {"foo.bar": 1}
    assert flatten(inp_dict) == exp_out