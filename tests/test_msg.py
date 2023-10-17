from moshi.msg import Message, ScoreL, ScoreY, Scores
from moshi.grade import Level, YesNo

def test_to_json():
    msg = Message('usr', 'hello')
    pld = msg.to_json()
    assert isinstance(pld, dict)
    assert pld['role'] == 'usr'

def test_scores():
    sco = ScoreL(Level.ADULT, "Because I say so.")
    print(sco)
    scos = Scores(
        vocab=sco,
        polite=ScoreY(YesNo.YES, "Something informative.")
    )
    print(scos)