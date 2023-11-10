from math import e, exp
from pprint import pprint
import time

import pytest

from moshi import Prompt, utils
from moshi.language import Language
from moshi.llmfx import vocab
from moshi.vocab import MsgV

@pytest.mark.parametrize('pf', vocab.PROMPT_FILES)
def test_parse_prompt(pf):
    """ Test that each prompt file can be parsed. """
    pro = Prompt.from_file(pf)


# TODO update for response_format JSON
@pytest.mark.openai
@pytest.mark.slow
def test_extract_all():
    """ Test that vocab terms can be extracted from a message. """
    msg = "私は行った"
    bcp47 = "ja-JP"
    t0 = time.time()
    vocs = vocab.extract_all(msg, bcp47=bcp47, detail=False)
    print(f"Extracted {len(vocs)} vocab terms in {time.time()-t0:.2f} seconds.")
    pprint(vocs)
    assert len(vocs) == 3
    assert "私" in vocs
    assert vocs["私"]["pos"] == "pronoun" 
    got_verb = False
    for term, v in vocs.items():
        assert v['defn'] is not None
        assert v['pos'] is not None
        if v["pos"] == "verb":
            assert not got_verb, "Only one verb should be extracted from the message '私は行った'."
            got_verb = True
            assert v["root"] is not None
            assert v["con"] is not None
    assert got_verb, "No verb was extracted from the message '私は行った', expected precisely one: '行く'."

@pytest.mark.parametrize("msg,eterms", [
    (
        "こんにちは、ケンと呼んでください。",
        ["こんにちは", "ケン", "と", "呼んで", "ください"]
    ),
])
@pytest.mark.openai
def test_vocab_extract_terms(msg: str, eterms: list[str]):
    terms: list[str] = vocab.extract_terms(msg)
    print(f"extracted terms: {terms}")
    assert isinstance(terms, list), "Invalid return type for extract_terms, expected a list."
    assert len(terms) == len(eterms), "Extracted different number of terms."
    incorrect_terms = 0
    for term, eterm in zip(terms, eterms):
        assert isinstance(term, str), "Invalid term type."
        if term != eterm:
            print(f"term: {term} != eterm: {eterm}")
            incorrect_terms += 1
    assert incorrect_terms == 0, f"Extracted {incorrect_terms} incorrect terms."

@pytest.mark.parametrize("msg,terms", [
    (
        "I went to the store.",
        ['I', 'went', 'to', 'the', 'store']
    ),
    (
        "店に行った",
        ['店', 'に', '行った']
    ),
], ids=["en", "ja"])
@pytest.mark.openai
def test_vocab_extract_pos(msg: str, terms: list[str]):
    vocs: dict[str, str] = vocab.extract_pos(msg, terms)
    pprint(vocs)
    assert isinstance(vocs, dict), "Invalid return type for extract_pos, expected a dict."
    for term, pos in vocs.items():
        assert isinstance(term, str), "Invalid term type."
        assert isinstance(pos, str), "Invalid pos type."
    assert set(vocs.keys()) == set(terms), "Extracted different terms."

@pytest.mark.parametrize("msg,terms,lang", [
    (
        'I went.',
        ['I', 'went'],
        Language("en-US")
    ),
    (
        '店に行った',
        ['店', 'に', '行った'],
        Language("ja-JP")
    )
], ids=["en", "ja"])
@pytest.mark.openai
def test_vocab_extract_defn(msg: str, terms: list[str], lang: Language):
    defns: dict[str, str] = vocab.extract_defn(msg, terms, lang=lang.name)
    pprint(defns)
    for term, defn in defns.items():
        assert term in terms
        assert isinstance(defn, str)
    assert len(defns) == len(terms), "Got different number of definitions than the number of terms provided."
    assert set(defns.keys()) == set(terms), "Got different defined terms than the terms provided."

@pytest.mark.parametrize("msg,terms,lang", [
    (
        'I went.',
        ['I', 'went'],
        Language("en-US")
    ),
    (
        '店に行った',
        ['店', 'に', '行った'],
        Language("ja-JP")
    )
], ids=["en", "ja"])
@pytest.mark.openai
def test_vocab_extract_udefn(msg: str, terms: list[str], lang: Language):
    udefns: dict[str, str] = vocab.extract_udefn(msg, terms, lang=lang.name)
    pprint(udefns)
    for term, udefn in udefns.items():
        assert term in terms
        assert isinstance(udefn, str)
    assert len(udefns) == len(terms), "Got different number of definitions than the number of terms provided."
    assert set(udefns.keys()) == set(terms), "Got different defined terms than the terms provided."

# TODO update for response_format JSON
@pytest.mark.openai
def test_vocab_extract_detail():
    term = "volcán"
    lang = Language("es-MS")
    detail = vocab.extract_detail(term, lang.name)
    print(detail)
    assert isinstance(detail, str)

@pytest.mark.openai
def test_vocab_extract_root():
    terms = ["行った", "明るく", "brightly", "lamentablemente"]
    expected_roots = ["行く", "明るい", "bright", "lamentable"]
    roots = vocab.extract_root(terms)
    print(roots)
    for (term, root), exprt in zip(roots.items(), expected_roots):
        assert term in terms
        assert isinstance(root, str)
        assert utils.similar(root, exprt) > 0.5

@pytest.mark.openai
def test_vocab_extract_verb_conjugation():
    verbs = ["行った"]
    econs = ["past"]
    cons: dict[str: str] = vocab.extract_verb_conjugation(verbs)
    pprint(cons)
    assert isinstance(cons, dict)
    assert len(cons) == len(econs), "Got different number of conjugations than the number of verbs provided."
    for verb, econ in zip(verbs, econs):
        assert verb in verbs, "LLM returned a conjugation for a verb that was not provided."
        con: str = cons[verb]
        assert utils.similar(con, econ) == 1.0 or con.startswith(econ), "Got different conjugation than expected for '{verb}': got='{con}', expected='{econ}'."

# TODO update for response_format JSON
@pytest.mark.openai
@pytest.mark.parametrize('term', ["行った", "明るく"])
def test_synonym(term):
    synos: list[str] = vocab.synonyms(term)
    print(synos)
    assert len(synos) > 0
    assert all([isinstance(syno, str) for syno in synos])

# TODO update for response_format JSON
@pytest.mark.openai
def test_extract_msgv():
    msg = "I went to the store and bought some milk."
    bcp47 = "en-US"
    msgvs = vocab.extract_msgv(msg, bcp47)
    for msgv in msgvs:
        print(msgv)
    assert len(msgvs) == 5
    expected_msgvs = [
        MsgV(bcp47=bcp47, term="went", pos="verb", udefn=""),
        MsgV(bcp47=bcp47, term="store", pos="noun", udefn=""),
        MsgV(bcp47=bcp47, term="bought", pos="verb", udefn=""),
        MsgV(bcp47=bcp47, term="milk", pos="noun", udefn=""),
    ]
    matched = 0
    for msgv in msgvs:
        for mv in expected_msgvs:
            if msgv.term == mv.term:
                matched += 1
                assert msgv.pos == mv.pos
                assert msgv.udefn == mv.udefn
                assert msgv.bcp47 == mv.bcp47
    assert matched >= len(expected_msgvs)