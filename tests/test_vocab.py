from datetime import datetime, timedelta
from more_itertools import first

import pytest

from moshi.vocab import Vocab, MsgV, UsageV, CurricV, select_vocabulary
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

def test_select_vocabulary():
    def _mock_usage(count: int, last: datetime) -> UsageV:
        """ Create a mock UsageV. """
        usgs = []
        first = last - timedelta(days=count)
        for i in range(count):
            dt = last - timedelta(days=i)
            usgs.append(Usage(tid=f'test_tid_{i}', mid=f'test_mid_{i}', when=dt))
        return UsageV(usgs=usgs, first=first, last=last)
    # Create a mock vocabulary dictionary
    vocs = {
        'apple': _mock_usage(count=2, last=datetime(2022, 1, 1)),
        'banana': _mock_usage(count=1, last=datetime(2022, 1, 2)),
        'cherry': _mock_usage(count=3, last=datetime(2022, 1, 3)),
        'date': _mock_usage(count=0, last=datetime(2022, 1, 4)),
        'elderberry': _mock_usage(count=2, last=datetime(2022, 1, 5)),
        'fig': _mock_usage(count=1, last=datetime(2022, 1, 6)),
        'grape': _mock_usage(count=4, last=datetime(2022, 1, 7)),
        'honeydew': _mock_usage(count=0, last=datetime(2022, 1, 8)),
    }

    # Test with default arguments
    selected = select_vocabulary(vocs)
    assert len(selected) == 8
    assert selected == ['apple', 'banana', 'cherry', 'date', 'elderberry', 'fig', 'grape', 'honeydew']

    # Test with a smaller max_usg value
    selected = select_vocabulary(vocs, max_usg=2)
    assert len(selected) == 4
    assert selected == ['banana', 'date', 'fig', 'honeydew']

    # Test with a smaller n value
    selected = select_vocabulary(vocs, n=3)
    assert len(selected) == 3
    assert selected == ['grape', 'cherry', 'elderberry']

    # Test with a recent datetime
    recent = datetime(2022, 1, 6)
    selected = select_vocabulary(vocs, recent=recent)
    assert len(selected) == 8
    assert selected == ['fig', 'banana', 'apple', 'elderberry', 'cherry', 'grape', 'date', 'honeydew']

    # Test with a combination of arguments
    selected = select_vocabulary(vocs, n=4, max_usg=1, recent=recent)
    assert len(selected) == 4
    assert selected == ['fig', 'banana', 'elderberry', 'apple']