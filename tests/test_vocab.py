import pytest

from moshi.vocab import Vocab, MsgV, UsageV, CurricV
from moshi.vocab.usage import Usage

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

def test_MsgV_init():
    voc = MsgV(
        term="test",
        bcp47="en-US",
        pos='noun',
    )
    from pprint import pprint
    print(voc)
    pprint(voc.model_dump())
    assert voc.pos == 'noun'


def test_usagev_init():
    voc = UsageV(
        term="test",
        bcp47="en-US",
        usgs=[Usage(tid='test_tid', mid='test_mid')],
    )
    from pprint import pprint
    print(voc)
    pprint(voc.model_dump())
    assert voc.correct == 0
    assert voc.incorrect == 0