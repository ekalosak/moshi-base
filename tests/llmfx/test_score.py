import pytest

from moshi import message
from moshi.grade import Level, YesNo
from moshi.llmfx import msg_score

def test_yesno():
    for yn in YesNo:
        YesNo.from_str(yn.name)
    print(YesNo.to_ranking())
    assert YesNo.YES > YesNo.NO
    assert YesNo.YES != YesNo.NO
    assert YesNo.YES - YesNo.NO > 1

def test_level():
    for l in Level:
        Level.from_str(l.name)
    print(Level.to_ranking())

@pytest.mark.openai
@pytest.mark.parametrize('msg, esco', [
    ("widgywadgDNA", Level.ERROR),
    ("milk", Level.BABY),
    ("applesauce", Level.CHILD),
    ("In oregano seven query jib", Level.ADULT),
    ("Criminal rats overtaken city", Level.ADULT),
    ("Gargantuan alternative grandeur paroxysm", Level.EXPERT),
])
def test_vocab(msg, esco):
    sco = msg_score.score_vocab(msg)
    print(f"Vocab score: {msg} -> {sco}")
    print(f"Explanation: {sco.explain}")
    assert isinstance(sco.explain, str)
    assert isinstance(sco.score, Level)
    assert abs(sco.score - esco) <= 1, "Level mismatch."

@pytest.mark.openai
@pytest.mark.parametrize('msg, esco', [
    ("In oregano seven query jib", Level.ERROR),
    ("have truck", Level.BABY),
    ("I have a truck", Level.CHILD),
    ("Rats have overtaken the city", Level.ADULT),
    ("Jeff has a great sense of humor, developed in his early childhood", Level.EXPERT),
])
def test_grammar(msg, esco: Level):
    sco = msg_score.score_grammar(msg)
    print(f"Grammar score: {msg} -> {sco}")
    print(f"Explanation: {sco.explain}")
    assert isinstance(sco.explain, str)
    assert isinstance(sco.score, Level)
    assert abs(sco.score - esco) <= 1, "Level mismatch."


@pytest.mark.openai
@pytest.mark.parametrize('msg, esco', [
    ("My name's Gregory, but please call me Greg.", YesNo.YES),
    ("Oregano is a favored herb", YesNo.SOMEWHAT),
    ("Knowing me, I can be Chuck ", YesNo.NO),
])
def test_idiom(msg, esco: YesNo):
    sco = msg_score.score_idiom(msg)
    print(f"Idiom score: {msg} -> {sco}")
    print(f"Explanation: {sco.explain}")
    assert isinstance(sco.explain, str)
    assert isinstance(sco.score, YesNo)
    assert abs(sco.score - esco) <= 1, "Score mismatch."

@pytest.mark.openai
@pytest.mark.parametrize('msg, esco', [
    ("You are a jerk", YesNo.NO),
    ("You are my friend", YesNo.MOSTLY),
    ("Hello, it's nice to meet you", YesNo.YES)
])
def test_polite(msg, esco):
    sco = msg_score.score_polite(msg)
    print(f"Politeness score: {msg} -> {sco}")
    print(f"Explanation: {sco.explain}")
    assert isinstance(sco.explain, str)
    assert isinstance(sco.score, YesNo)
    assert abs(sco.score - esco) <= 1, "Score mismatch."

@pytest.mark.openai
@pytest.mark.parametrize('msgs, esco', [
    ([message('ast', "Hi, I'm George."), message('usr', "Hi George, I'm Charlie.")], YesNo.YES),
    ([message('ast', "Hi, I'm George."), message('usr', "Quack quack")], YesNo.NO),
    ([message('sys', "Pretend you're a duck"), message('ast', "Hi, I'm George."), message('usr', "Quack quack")], YesNo.MOSTLY),
])
def test_context(msgs, esco):
    sco = msg_score.score_context(msgs)
    print(f"Context appropriate score: {msgs} -> {sco}")
    print(f"Explanation: {sco.explain}")
    assert isinstance(sco.explain, str)
    assert isinstance(sco, YesNo)
    assert abs(sco.score - esco) <= 1, "Score mismatch."