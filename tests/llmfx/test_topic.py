from moshi import Prompt, Message
from moshi.activ import MinPl
from moshi.llmfx import topics
from moshi.transcript import Transcript

def test_get():
    pla = MinPl(
        uid="test-user",
        bcp47="en-US",
    )
    tra = Transcript.from_plan(pla)
    tra.messages = [
        Message('ast', "Hello, world!"),
        Message('usr', "Hey what's up, I'm Mars."),
        Message('ast', "Ah, and I, Jupiter."),
        Message('usr', "Celestial, my dude."),
        Message('ast', "Indeed, my friend."),
        Message('usr', "So, what's the deal with the sun?"),
        Message('ast', "It's a star some minutes away."),
    ]
    tops = topics.extract(tra)
    print(tops)
    assert isinstance(tops, list)
    for top in tops:
        assert isinstance(top, str)