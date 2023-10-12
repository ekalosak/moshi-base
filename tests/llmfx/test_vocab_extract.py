from pprint import pprint

import pytest

from moshi import Vocab, Prompt
from moshi.llmfx import vocab

def test_parse_prompt():
    pro = Prompt.from_file(vocab.POS_PROMPT_FILE)

@pytest.mark.parametrize("msg", ["I went to the store."])
@pytest.mark.openai
def test_vocab_extract_pos(msg: str):
    vocs = vocab._extract_pos(msg)
    pprint(vocs)
    assert all([isinstance(v, Vocab) for v in vocs])
    for v in vocs:
        assert v.pos is not None
        assert v.term is not None