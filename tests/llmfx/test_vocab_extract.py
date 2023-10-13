from pprint import pprint

import pytest

from moshi import Vocab, Prompt
from moshi.llmfx import vocab

@pytest.mark.parametrize('pf', vocab.PROMPT_FILES)
def test_parse_prompt(pf):
    pro = Prompt.from_file(pf)

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