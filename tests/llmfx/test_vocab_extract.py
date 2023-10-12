from pprint import pprint

import pytest

from moshi import Message, Role, Vocab, Prompt
from moshi.llmfx import vocab

def test_parse_prompt():
    pro = Prompt.from_file(vocab.POS_PROMPT_FILE)

@pytest.mark.parametrize("msg", ["I went to the store."])
@pytest.mark.openai
def test_vocab_extract(msg: str):
    vocs = vocab.extract(msg)
    pprint(vocs)
    assert all([isinstance(v, Vocab) for v in vocs])