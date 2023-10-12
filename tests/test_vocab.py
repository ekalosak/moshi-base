from moshi import Vocab

def test_vocab_init():
    vocab = Vocab(term="test", term_translation="test", part_of_speech="test", definition="test", definition_translation="test")
    assert vocab.term == "test"
    assert vocab.translations == {"term_translation": None}
    assert vocab.pos == "test"
    assert vocab.defn == "test"
    assert vocab.bcp47 == None
    assert vocab.root == None
    assert vocab.conj == None