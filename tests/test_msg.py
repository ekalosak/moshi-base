from moshi.grade import Level, YesNo, Score, Scores
from moshi.msg import message

def test_to_json():
    msg = message('usr', 'hello')
    pld = msg.to_json()
    assert isinstance(pld, dict)
    assert pld['role'] == 'usr'

def test_scores():
    sco = Score(Level.ADULT, "Because I say so.")
    print(sco)
    scos = Scores(
        vocab=sco,
        polite=Score(YesNo.YES, "Something informative.")
    )
    print(scos)