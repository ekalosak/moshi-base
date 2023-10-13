from pprint import pprint
import time

import pytest

from moshi import Vocab, Prompt, utils
from moshi.llmfx import grammar

def test_parse_prompt():
    pro = Prompt.from_file(grammar.PROMPT_FILE)

@pytest.mark.openai
def test_explain():
    msg = "Yo soy un burrito."
    print(msg)
    expl = grammar.explain(msg)
    print(expl)
    assert expl is not None
    assert isinstance(expl, str)
    assert expl != ""
    assert len(expl) > 10, "Expected a longer explanation."