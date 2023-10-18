from moshi import Message
from moshi.activ import MinPl
from moshi.grade import Grade
from moshi.llmfx import tra_score as score
from moshi.transcript import Transcript

def test_grade():
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
    print(tra.to_templatable())
    gd = score.grade(tra) 
    print(gd)
    assert isinstance(gd, Grade)