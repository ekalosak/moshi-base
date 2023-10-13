from pprint import pprint
import time

import pytest

from moshi import Message, Prompt
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

def test_msg_grammar():
    msg = Message('usr', "Yo soy un burrito.", grammar="In this simple subject-verb-object sentence, 'Yo' is the subject, 'soy' is the verb, and 'un burrito' is the object. The subject is the person or thing that performs the action, the verb is the action, and the object is the person or thing that receives the action. Here, the speaker humoursly refers to themself as a burrito.")