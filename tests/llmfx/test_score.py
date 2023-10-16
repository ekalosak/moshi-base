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