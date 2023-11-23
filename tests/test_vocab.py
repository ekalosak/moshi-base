from datetime import datetime, timedelta, timezone

from moshi.vocab import Vocab, MsgV, UsageV
from moshi.vocab.plan import select_vocabulary
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
    # TODO CONTINUE actually run this test
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
        'apple': _mock_usage(count=2, last=datetime(2022, 1, 1, tzinfo=timezone.utc)),
        'banana': _mock_usage(count=1, last=datetime(2022, 1, 2, tzinfo=timezone.utc)),
        'cherry': _mock_usage(count=3, last=datetime(2022, 1, 3, tzinfo=timezone.utc)),
        'date': _mock_usage(count=1, last=datetime(2022, 1, 4, tzinfo=timezone.utc)),
        'elderberry': _mock_usage(count=2, last=datetime(2022, 1, 5, tzinfo=timezone.utc)),
        'fig': _mock_usage(count=1, last=datetime(2022, 1, 6, tzinfo=timezone.utc)),
        'grape': _mock_usage(count=4, last=datetime(2022, 1, 7, tzinfo=timezone.utc)),
        'honeydew': _mock_usage(count=0, last=datetime(2022, 1, 8, tzinfo=timezone.utc)),
    }

    # Test with default arguments
    selected = select_vocabulary(vocs, max_usg=4)
    assert len(selected) == 7, "grape should be dropped with max_usg=4"
    assert selected == ['apple', 'banana', 'cherry', 'date', 'elderberry', 'fig', 'honeydew']

    # Test with a smaller max_usg value
    selected = select_vocabulary(vocs, max_usg=2)
    assert len(selected) == 4
    assert selected == ['banana', 'date', 'fig', 'honeydew']

    # Test with a smaller n value
    selected = select_vocabulary(vocs, n=3)
    assert len(selected) == 3
    assert selected == ['honeydew', 'fig', 'elderberry'], "grape should be dropped with max_usg=4"

    # Test with a recent datetime
    recent = datetime(2022, 1, 6, tzinfo=timezone.utc)
    selected = select_vocabulary(vocs, recent=recent)
    assert len(selected) == 6
    assert selected == [v for v in vocs if v not in ('grape', 'honeydew')], f"grape and honeydew should be dropped with recent={recent}"

    # Test with a combination of arguments
    recent = datetime(2022, 1, 5, tzinfo=timezone.utc)
    selected = select_vocabulary(vocs, n=4, max_usg=2, recent=recent)
    assert len(selected) == 2
    assert selected == ['banana', 'date']