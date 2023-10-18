import pytest

from moshi import Message
from moshi.activ import MinPl
from moshi.grade import Grade
from moshi.llmfx import tra_score as score
from moshi.transcript import Transcript

@pytest.fixture
def pla():
    return MinPl(
        uid="test-user",
        bcp47="en-US",
    )

_msgs1 = [
    Message('ast', "Hello, world!"),
    Message('usr', "Hey what's up, I'm Mars."),
    Message('ast', "Ah, and I, Jupiter."),
    Message('usr', "Celestial, my dude."),
    Message('ast', "Indeed, my friend."),
    Message('usr', "So, what's the deal with the sun?"),
    Message('ast', "It's a star some minutes away."),
]
_msgs2 = [
    Message('ast', "¿Que quieres beber?"),
    Message('usr', "Donde estas el biblioteca"),
]
_msgs3 = [
    Message('ast', "逃げろ、火山が噴火した"),
    Message('usr', "すみません、火山って何ですか？"),
]

@pytest.fixture(params=[_msgs1, _msgs2, _msgs3, []], ids=['celestial', 'troglodyte', 'newb', 'empty'])
def msgs(request) -> list[Message]:
    return request.param

@pytest.fixture
def tra(msgs, pla):
    tra = Transcript.from_plan(pla)
    tra.messages = msgs
    print(tra.to_templatable())
    return tra


@pytest.mark.openai
def test_grade(tra: Transcript):
    gd = score.grade(tra) 
    print(gd)
    assert isinstance(gd, Grade)


@pytest.mark.openai
def test_skill_assess(tra):
    skills = score.summarize_skills(tra)
    print(skills)
    assert isinstance(skills, str)

@pytest.mark.openai
def test_split_str_wk():
    summary = """The user has good grammar, but poor vocabulary."""
    st, wk = score.split_into_str_and_weak(summary)
    print(f"Strengths: {st}")
    print(f"Weaknesses: {wk}")
    for s in [st, wk]:
        assert isinstance(s, str)
        assert '\n' not in s
    assert 'grammar' in st
    assert 'vocab' in wk