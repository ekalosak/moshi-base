import pytest

from moshi.vocab import Vocab, MsgV, UsageV, CurricV

def test_Vocab_init():
    voc = Vocab(
        term="test",
        bcp47="en-US",
    )
    from pprint import pprint
    print(voc)
    pprint(voc.model_dump())
    assert voc.term == "test"

def test_Vocab_lang():
    voc = Vocab(
        term="test",
        bcp47="en-US",
    )
    assert voc.lang.bcp47 == "en-US"

@pytest.mark.parametrize('pos', [None, 'noun'])
def test_MsgV_init(pos):
    voc = MsgV(
        term="test",
        bcp47="en-US",
        pos=pos,
    )
    from pprint import pprint
    print(voc)
    pprint(voc.model_dump())
    assert voc.pos == pos


def test_usagev_init():
    voc = UsageV(
        term="test",
        bcp47="en-US",
        usage="test",
    )
    from pprint import pprint
    print(voc)
    pprint(voc.model_dump())
    assert voc.usage == "test"