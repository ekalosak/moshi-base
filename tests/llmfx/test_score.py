import pytest

from moshi import Message, Role
from moshi.llmfx import msg_score

@pytest.mark.openai
@pytest.mark.parametrize('msg, sco', [("I like apples", 2.5), ("Criminal rats overtaken city", 4.0), ("Gargantuan alternative grandeur", 7.0)])
def test_msg_score_vocab(msg, sco):
    vsco = msg_score.score_vocab(msg)
    print(f"Vocab score: {msg} -> {vsco}")
    assert vsco <= 10
    assert vsco >= 1
    assert abs(vsco - sco) < 2.5, "Vocab score mismatch."

@pytest.mark.openai
@pytest.mark.parametrize('msg, sco', [("I like apples", 2.0), ("Rats overtaken city", 1.5), ("Rats have overtaken the city", 5.5), ("Jeff has a great sense of humor, developed in his early childhood", 7.5)])
def test_msg_score_grammar(msg, sco):
    gsco, expl = msg_score.score_grammar(msg)
    print(f"Grammar score: {msg} -> {gsco}")
    print(f"Explanation: {expl}")
    assert isinstance(expl, str)
    assert isinstance(gsco, float)
    assert gsco <= 10
    assert gsco >= 1
    assert abs(gsco - sco) < 2.5, "Grammar score mismatch."

@pytest.mark.openai
@pytest.mark.parametrize('msg, sco', [("You are a jerk", 1.0), ("You are my friend", 10.0)])
def test_msg_score_politeness(msg, sco):
    psco, expl = msg_score.score_politeness(msg)
    print(f"Politeness score: {msg} -> {psco}")
    print(f"Explanation: {expl}")
    assert isinstance(expl, str)
    assert isinstance(psco, float)
    assert psco <= 10
    assert psco >= 1
    assert abs(psco - sco) < 2.5, "Politeness score mismatch."