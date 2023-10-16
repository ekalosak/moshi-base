import pytest

from moshi import Message
from moshi.grade import Level, YesNo
from moshi.llmfx import msg_score

def test_level():
    print(Level.to_ranking())

def test_yesno():
    print(YesNo.to_ranking())

@pytest.mark.openai
@pytest.mark.parametrize('msg, esco', [
    ("widgywadgDNA", Level.ERROR),
    ("milk", Level.BABY),
    ("applesauce", Level.CHILD),
    ("In oregano seven query jibb", Level.ADULT),
    ("Criminal rats overtaken city", Level.ADULT),
    ("Gargantuan alternative grandeur paroxysm", Level.EXPERT),
])
def test_vocab(msg, esco):
    sco, expl = msg_score.score_vocab(msg)
    print(f"Vocab score: {msg} -> {sco}")
    print(f"Explanation: {expl}")
    assert isinstance(expl, str)
    assert isinstance(sco, Level)
    assert abs(sco - esco) <= 1, "Level mismatch."

@pytest.mark.openai
@pytest.mark.parametrize('msg, esco', [
    ("In oregano seven query jib", Level.ERROR),
    ("I like apple", Level.BABY),
    ("I like apples", Level.CHILD),
    ("Rats overtaken city", Level.CHILD),
    ("Rats have overtaken the city", Level.ADULT),
    ("Jeff has a great sense of humor, developed in his early childhood", Level.EXPERT),
])
def test_grammar(msg, esco: Level):
    sco, expl = msg_score.score_grammar(msg)
    print(f"Grammar score: {msg} -> {sco}")
    print(f"Explanation: {expl}")
    assert isinstance(expl, str)
    assert isinstance(sco, Level)
    assert abs(sco - esco) <= 1, "Level mismatch."


@pytest.mark.openai
@pytest.mark.parametrize('msg, esco', [
    ("My name's Charlie, but you can call me Chuck.", YesNo.YES),
    ("Those calling me Chuck know me", YesNo.SLIGHT),
    ("Knowing me, I can be Chuck ", YesNo.NO),
])
def test_idiom(msg, esco: YesNo):
    sco, expl = msg_score.score_idiom(msg)
    print(f"Idiom score: {msg} -> {sco}")
    print(f"Explanation: {expl}")
    assert isinstance(expl, str)
    assert isinstance(sco, Level)
    assert abs(sco - esco) <= 1, "Score mismatch."

@pytest.mark.openai
@pytest.mark.parametrize('msg, esco', [
    ("You are a jerk", YesNo.NO),
    ("You are my friend", YesNo.MOSTLY),
    ("Hello, it's nice to meet you", YesNo.YES)
])
def test_polite(msg, esco):
    sco, expl = msg_score.score_polite(msg)
    print(f"Politeness score: {msg} -> {sco}")
    print(f"Explanation: {expl}")
    assert isinstance(expl, str)
    assert isinstance(sco, YesNo)
    assert abs(sco - esco) <= 1, "Score mismatch."

@pytest.mark.openai
@pytest.mark.parametrize('msgs, esco', [
    ([Message('ast', "Hi, I'm George."), Message('usr', "Hi George, I'm Charlie.")], YesNo.YES),
    ([Message('ast', "Hi, I'm George."), Message('usr', "Quack quack")], YesNo.NO),
    ([Message('sys', "Pretend you're a duck"), Message('ast', "Hi, I'm George."), Message('usr', "Quack quack")], YesNo.MOSTLY),
])
def test_contextual(msgs, esco):
    sco, expl = msg_score.score_context(msgs)
    print(f"Context appropriate score: {msgs} -> {sco}")
    print(f"Explanation: {expl}")
    assert isinstance(expl, str)
    assert isinstance(sco, YesNo)
    assert abs(sco - esco) <= 1, "Score mismatch."