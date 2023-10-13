from pprint import pprint
import time

import pytest

from moshi import Vocab, Prompt, utils
from moshi.llmfx import vocab

@pytest.mark.parametrize('pf', vocab.PROMPT_FILES)
def test_parse_prompt(pf):
    pro = Prompt.from_file(pf)

@pytest.mark.openai
def test_extract():
    msg = "私は行った"
    bcp47 = "ja-JP"
    t0 = time.time()
    vocs = vocab.extract(msg, bcp47=bcp47, detail=False)
    print(f"Extracted {len(vocs)} vocab terms in {time.time()-t0:.2f} seconds.")
    pprint(vocs)
    assert len(vocs) == 3
    assert vocs[0].term == "私"
    assert vocs[0].pos == "pronoun"
    got_verb = False
    for v in vocs:
        assert v.defn is not None
        assert v.pos is not None
        if v.pos == "verb":
            assert not got_verb, "Only one verb should be extracted from the message '私は行った'."
            got_verb = True
            assert v.root is not None
            assert v.conju is not None
    assert got_verb, "No verb was extracted from the message '私は行った', expected precisely one: '行く'."

@pytest.mark.parametrize("msg", ["I went to the store."])
@pytest.mark.openai
def test_vocab_extract_pos(msg: str):
    vocs = vocab._extract_pos(msg)
    pprint(vocs)
    assert all([isinstance(v, Vocab) for v in vocs])
    for v in vocs:
        assert v.pos is not None
        assert v.term is not None

@pytest.mark.openai
def test_vocab_extract_defn():
    vocs = [
        Vocab(term="I", bcp47="en-us"),
        Vocab(term="went", bcp47="en-us"),
    ]
    pprint(vocs)
    vocab._extract_defn(vocs=vocs)
    pprint(vocs)
    for v in vocs:
        assert v.defn is not None

@pytest.mark.openai
def test_vocab_extract_detail():
    voc = Vocab(term="volcán", bcp47="es-MS")
    assert voc.detail is None
    vocab._extract_detail(voc)
    print(voc)
    assert voc.detail is not None

@pytest.mark.openai
def test_vocab_extract_verb_root():
    voc = Vocab(term="行った", bcp47="ja-JP", pos="verb")
    assert voc.root is None
    vocab._extract_verb_root([voc])
    print(voc)
    assert voc.root is not None
    assert voc.root != voc.term
    assert utils.similar(voc.root, "行く") > 0.5

@pytest.mark.openai
def test_vocab_extract_verb_conjugation():
    voc = Vocab(term="行った", bcp47="ja-JP", pos="verb")
    assert voc.conju is None
    vocab._extract_verb_conjugation([voc])
    print(voc)
    assert voc.conju is not None
    assert voc.conju != voc.term
    assert utils.similar(voc.conju, "past") == 1.0
