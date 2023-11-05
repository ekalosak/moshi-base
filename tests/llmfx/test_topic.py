import pytest

from moshi import message
from moshi.activ import MinPl
from moshi.llmfx import topics
from moshi.transcript import Transcript

@pytest.mark.openai
def test_get_topics():
    """ Test that we can extract a topic e.g. 'outer space' from a transcript. """
    pla = MinPl(
        uid="test-user",
        bcp47="en-US",
    )
    tra = Transcript.from_plan(pla)
    tra.add_msgs([
        message('ast', "Hello, world!"),
        message('usr', "Hey what's up, I'm Mars."),
        message('ast', "Ah, and I, Jupiter."),
        message('usr', "Celestial, my dude."),
        message('ast', "Indeed, my friend."),
        message('usr', "So, what's the deal with the sun?"),
        message('ast', "It's a star some minutes away."),
    ])
    tops = topics.extract(tra)
    print(tops)
    assert isinstance(tops, list)
    for top in tops:
        assert isinstance(top, str)