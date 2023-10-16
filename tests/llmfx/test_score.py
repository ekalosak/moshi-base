import pytest

from moshi import Level
from moshi.llmfx import msg_score

def test_level():
    print(Level.to_ranking())

@pytest.mark.openai
@pytest.mark.parametrize('msg, sco', [("I like apples", 2.5), ("Criminal rats overtaken city", 4.0), ("Gargantuan alternative grandeur", 7.0)])
def test_vocab(msg, sco):
    vsco = msg_score.score_vocab(msg)
    print(f"Vocab score: {msg} -> {vsco}")
    assert vsco <= 10
    assert vsco >= 1
    assert abs(vsco - sco) < 2.5, "Vocab score mismatch."

@pytest.mark.openai
@pytest.mark.parametrize('msg, sco', [("I like apples", Level.CHILD), ("Rats overtaken city", Level.CHILD), ("Rats have overtaken the city", Level.ADULT), ("Jeff has a great sense of humor, developed in his early childhood", Level.EXPERT)])
def test_grammar(msg, sco: Level):
    gsco, expl = msg_score.score_grammar(msg)
    print(f"Grammar score: {msg} -> {gsco}")
    print(f"Explanation: {expl}")
    assert isinstance(expl, str)
    assert isinstance(gsco, Level)
    assert abs(gsco - sco) <= 1, "Grammar level mismatch."

@pytest.mark.openai
@pytest.mark.parametrize('msg, sco', [("You are a jerk", 1.0), ("You are my friend", 10.0)])
def test_polite(msg, sco):
    psco, expl = msg_score.score_polite(msg)
    print(f"Politeness score: {msg} -> {psco}")
    print(f"Explanation: {expl}")
    assert isinstance(expl, str)
    assert isinstance(psco, float)
    assert psco <= 10
    assert psco >= 1
    assert abs(psco - sco) < 2.5, "Politeness score mismatch."
