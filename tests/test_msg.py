from moshi.msg import Message

def test_to_json():
    msg = Message('usr', 'hello')
    pld = msg.to_json()
    assert isinstance(pld, dict)
    assert pld['role'] == 'usr'