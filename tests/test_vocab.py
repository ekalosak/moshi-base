from moshi import Vocab

def test_vocab_init():
    voc = Vocab(
        term="test",
        pos="test",
        defn="test",
        bcp47="en-US",
    )
    from pprint import pprint
    print(voc)
    pprint(voc.model_dump())
    assert voc.term == "test"
    assert voc.part_of_speech == "test"
    assert voc.definition == "test"