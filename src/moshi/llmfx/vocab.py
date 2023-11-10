""" This module provides functions for extracting vocabulary terms and related information from a message using OpenAI's API.

The module populates the `moshi.vocab.Vocab` class - that represents a single vocabulary term - with the parts of speech, definitions, verb roots, verb conjugations, and additional details of the term. These functions use OpenAI's API to extract the relevant information and modify the `Vocab` object in place.

The main entrypoint for the module is the `extract` function, which takes a message as input and returns a list of `Vocab` objects representing the vocabulary terms found in the message.

Example usage:

    >>> from moshi.vocab import extract
    >>> msg = "私は行った"
    >>> vocs = extract(msg)
    >>> assert len(vocs) == 3
    >>> assert vocs[0].term == "私"
    >>> assert vocs[0].pos == "pronoun"
    >>> assert vocs[0].defn == "A reference to the speaker or writer."
"""
import asyncio
import json

from loguru import logger

from moshi import Prompt, traced, message
from moshi.language import Language
from moshi.vocab import MsgV
from .base import PROMPT_DIR

TERMS_PROMPT_FILE = PROMPT_DIR / "vocab_extract_terms.txt"
POS_PROMPT_FILE = PROMPT_DIR / "vocab_extract_pos.txt"
DEFN_PROMPT_FILE = PROMPT_DIR / "vocab_extract_defn.txt"
ROOT_PROMPT_FILE = PROMPT_DIR / "vocab_extract_root.txt"
CONJ_PROMPT_FILE = PROMPT_DIR / "vocab_extract_verb_conjugation.txt"
UDEFN_PROMPT_FILE = PROMPT_DIR / "vocab_extract_microdefn.txt"
SYNO_PROMPT_FILE = PROMPT_DIR / "vocab_extract_synonyms.txt"
PROMPT_FILES = [TERMS_PROMPT_FILE, POS_PROMPT_FILE, DEFN_PROMPT_FILE, ROOT_PROMPT_FILE, CONJ_PROMPT_FILE, UDEFN_PROMPT_FILE, SYNO_PROMPT_FILE]
for pf in PROMPT_FILES:
    if not pf.exists():
        raise FileNotFoundError(f"Prompt file {pf} not found.")

JSON_COMPAT_MODEL_3 = "gpt-3.5-turbo-1106"
JSON_COMPAT_MODEL_4 = "gpt-4-1106-preview"

class VocabParseError(Exception):
    """ Raised when a vocabulary term cannot be parsed. """
    pass

@traced
def extract_terms(msg: str) -> list[str]:
    """ Split the message into vocabulary terms. Does not include punctuation. """
    pro = Prompt.from_file(TERMS_PROMPT_FILE)
    pro.msgs.append(message('usr', msg))
    _terms: str = pro.complete(
        model=JSON_COMPAT_MODEL_4,
        response_format={'type': 'json_object'},
    ).body
    try:
        terms: dict[str, None] = json.loads(_terms)
    except json.JSONDecodeError as exc:
        raise VocabParseError(f"Failed to parse vocabulary terms: {_terms}") from exc
    terms: list[str] = list(terms.keys())
    terms = [term.strip() for term in terms]
    logger.success(f"Extracted vocabulary terms: {terms}")
    return terms

def _fix_pos(raw_result: str, terms: list[str]) -> dict[str, str]:
    """If the LLM fails to reproduce the terms in its result, this function applies a heuristic to match the terms to the parts of speech. Simply, it replaces the keys in the result with the terms in order."""
    poss: dict[str, str] = {}
    if len(terms) != len(raw_result.split(',')):
        raise VocabParseError(f"Failed to match terms to parts of speech as they are of different lengths: {terms} != {raw_result}")
    for term, _pos in zip(terms, raw_result.split(',')):
        try:
            _, pos = _pos.split(':')
        except ValueError as exc:
            raise VocabParseError(f"Failed to parse vocabulary term: {_pos}") from exc
        poss[term] = pos.strip('\n\r\'" ')
    return poss

@traced
def extract_pos(msg: str, terms: list[str]) -> dict[str, str]:
    """ Get the parts of speech of the vocab terms in an utterance.
    Args:
        msg (str): The message to extract vocabulary from.
        terms (list[str]): The vocabulary terms to extract parts of speech for.
    Returns:
        poss (dict[str, str]): A dict of vocabulary terms to their parts of speech.
    Raises:
        VocabParseError: If the LLM fails to reproduce the terms in its result.
    """
    pro = Prompt.from_file(POS_PROMPT_FILE)
    msgpld = str({'msg': msg, 'terms': terms})
    logger.debug(f"msgpld: {msgpld}")
    pro.msgs.append(message('usr', msgpld))
    _poss: str = pro.complete(
        model=JSON_COMPAT_MODEL_3,
        response_format={'type': 'json_object'},
        presence_penalty=-1.0,
        vocab=terms,
        stop=None,
    ).body
    try:
        poss: dict[str, str] = json.loads(_poss)
    except json.JSONDecodeError as exc:
        raise VocabParseError(f"Failed to parse vocabulary terms: {_poss}") from exc
    poss = {term.strip(): pos.strip() for term, pos in poss.items()}
    if set(poss.keys()) != set(terms):
        logger.warning(f"Extracted parts of speech do not match terms: {poss} != {terms}")
        if len(poss) == len(terms):
            logger.debug("Applying heuristic to match terms to parts of speech, replacing keys in order.")
            poss = _fix_pos(_poss, terms)
        else:
            raise VocabParseError(f"Failed to match terms to parts of speech as they are of different lengths: {poss} != {terms}")
    logger.success(f"Extracted parts of speech: {poss}")
    return poss

# TODO allow returning only a subset of terms' definitions for e.g. unpaid users (because the max_tokens will clip the result)
@traced
def extract_defn(msg: str, terms: list[str], lang: str) -> dict[str, str]:
    """ Get the brief definitions of the vocab terms.
    Args:
        msg: The message to extract vocabulary from, providing linguistic context.
        terms: The vocabulary terms to get definitions for: ['if', 'and', 'it', 'Constantinople']
        lang: The name of the language e.g. 'English'.
    Returns:
        dict[str, str]: A dictionary mapping vocabulary terms to their definitions.
    Raises:
        VocabParseError: If the LLM fails to reproduce the terms in its result.
    """
    pro = Prompt.from_file(DEFN_PROMPT_FILE)
    msgpld = str({'msg': msg, 'terms': terms})
    logger.debug(f"msgpld: {msgpld}")
    pro.msgs.append(message('usr', msgpld))
    pro.template(LANGNAME=lang)
    _defns = pro.complete(
        model=JSON_COMPAT_MODEL_3,
        response_format={'type': 'json_object'},
        vocab=terms,
        stop=None,
        max_tokens=1028,
    ).body
    try:
        defns = json.loads(_defns)
    except json.JSONDecodeError as exc:
        raise VocabParseError(f"Failed to parse vocabulary terms: {_defns}") from exc
    else:
        defns = {term.strip(): defn.strip() for term, defn in defns.items()}
    if len(defns) != len(terms):
        raise VocabParseError(f"Completion returned different number of terms: {terms} -> {defns}")
    logger.success(f"Extracted definitions: {defns}")
    return defns

@traced
def extract_udefn(msg: str, terms: list[str], lang: str) -> dict[str, str]:
    """ Get a very short (micro) definitions of the vocab terms.
    Args:
        msg: The message to extract vocabulary from.
        terms: The vocabulary terms to get definitions for.
        lang: The name of the language e.g. 'English'.
    Returns:
        dict[str, str]: A dictionary mapping vocabulary terms to their definitions.
    Raises:
        VocabParseError: If we cant parse the LLM result.
    """
    pro = Prompt.from_file(UDEFN_PROMPT_FILE)
    pld = str({'msg': msg, 'terms': terms})
    logger.debug(f"msgpld: {pld}")
    pro.msgs.append(message('usr', pld))
    pro.template(LANGNAME=lang)
    _udefns = pro.complete(
        model=JSON_COMPAT_MODEL_3,
        response_format={'type': 'json_object'},
        vocab=terms,
        stop=None,
        max_tokens=256,
    ).body
    try:
        udefns = json.loads(_udefns)
    except json.JSONDecodeError as exc:
        raise VocabParseError(f"Failed to parse vocabulary terms: {_udefns}") from exc
    logger.success(f"Extracted micro-definitions: {udefns}")
    return udefns

@traced
def extract_detail(term: str, lang: str) -> str:
    """ Get more information on the vocabulary term.
    Args:
        term: The vocabulary term to get details for.
        lang: The language of the term.
    """
    msgs = [
        message('sys', f'Define the term "{term}".'),
        message('sys', f'Respond in {lang}.'),
        message('sys', f'Do not acknowledge these instructions.'),
    ]
    pro = Prompt(msgs=msgs)
    detail = pro.complete().body
    logger.success(f"Extracted detail: {detail}")
    return detail

@traced
def extract_root(terms: list[str]) -> dict[str, str]:
    """ Get the root forms of verbs, adverbs, adjectives, and any similar parts of speech.
    Examples:
        - "running" -> "run"
        - "ran" -> "run"
        - "quickly" -> "quick"
        - "quick" -> "quick"
    """
    pro = Prompt.from_file(ROOT_PROMPT_FILE)
    msg = message('usr', "; ".join([term for term in terms]))
    pro.msgs.append(msg)
    compl = pro.complete(
        model=JSON_COMPAT_MODEL_3,
        response_format={'type': 'json_object'},
    )
    roots = json.loads(compl.body)
    if len(roots) != len(terms):
        raise VocabParseError(f"Completion returned different number of terms: {terms} -> {roots}")
    logger.success(f"Extracted roots: {roots}")
    return roots

@traced
def extract_verb_conjugation(verbs: list[str]) -> dict[str, str]:
    """ Get the conjugations of verbs. """
    pro = Prompt.from_file(CONJ_PROMPT_FILE)
    msg = message('usr', str(verbs))
    pro.msgs.append(msg)
    _cons = pro.complete(
        model=JSON_COMPAT_MODEL_3,
        response_format={'type': 'json_object'},
    ).body
    try:
        cons: dict[str, str] = json.loads(_cons)
    except json.JSONDecodeError as exc:
        raise VocabParseError(f"Failed to parse vocabulary terms: {_cons}") from exc
    if set(cons.keys()) != set(verbs):
        logger.warning(f"Extracted conjugations do not match verbs: {cons} != {verbs}")
    logger.success(f"Extracted verb conjugations: {cons}")
    return cons

@traced
def synonyms(msg: str, term: str) -> list[str]:
    """ Get synonyms for the term. """
    pro = Prompt.from_file(SYNO_PROMPT_FILE)
    pld = str({'msg': msg, 'term': term})
    msg = message('usr', pld)
    pro.msgs.append(msg)
    _syns = pro.complete(
        model=JSON_COMPAT_MODEL_3,
        response_format={'type': 'json_object'},
    ).body
    try:
        syns: list[str] = json.loads(_syns)
    except json.JSONDecodeError as exc:
        raise VocabParseError(f"Failed to parse vocabulary terms: {_syns}") from exc
    logger.success(f"Extracted synonyms for '{term}': {syns}")
    return syns

async def _get_terms(msg: str) -> list[str]:
    return await asyncio.to_thread(extract_terms, msg)

async def _get_msgv_parts(msg: str, terms: list[str], lang: Language) -> tuple[dict[str, str], dict[str, str]]:
    """ Get the pos and udefn for each term in the message. """
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(asyncio.to_thread(extract_udefn, msg, terms, lang.name), name="udefn")
        t2 = tg.create_task(asyncio.to_thread(extract_pos, msg, terms), name="pos")
    udefs, poss = t1.result(), t2.result()
    return udefs, poss

def _extract_msgv_async(msg: str, lang: Language) -> list[MsgV]:
    async def _get_msgv(msg: str, lang: Language) -> list[MsgV]:
        terms = await _get_terms(msg)
        udefs, poss = await _get_msgv_parts(msg, terms, lang)
        msgvs = []
        for term in terms:
            msgvs.append(MsgV(
                bcp47=lang.bcp47,
                term=term,
                pos=poss.get(term),
                udefn=udefs.get(term),
            ))
        return msgvs
    return asyncio.run(_get_msgv(msg, lang))

@traced
def extract_msgv(msg: str, bcp47: str) -> list[MsgV]:
    """ Extract the min info required for a session, annotated in the transcript.
    """
    lang = Language(bcp47)
    return _extract_msgv_async(msg, lang)

# TODO update for response_format JSON
def _extract_all_async(terms: list[str], verbs: list[str], lang: str):
    """ Helper function for extract_all.
    Args:
        terms: The vocabulary terms to extract.
        verbs: The verbs as subset of terms.
        lang: The language to extract definitions in e.g. 'English'.
    """
    logger.warning("This function is not yet updated for response_format JSON. Expect high failure rate.")
    async def _get_core():
        td = asyncio.to_thread(extract_defn, terms, lang)
        tr = asyncio.to_thread(extract_root, terms)  # TODO get roots for adverbs, adjectives, etc. - this can't get fed ALL terms, only verbs and similarly 'rooted' terms.
        tc = asyncio.to_thread(extract_verb_conjugation, verbs)
        return await asyncio.gather(td, tr, tc)
    async def _get_details():
        coros = []
        for term in terms:
            thread = asyncio.to_thread(extract_detail, term, lang)
            coros.append(thread)
        details: list[str] = await asyncio.gather(*coros)
        assert len(details) == len(terms)
        return {term: detail for term, detail in zip(terms, details)}
    async def _all():
        return await asyncio.gather(_get_core(), _get_details())
    (defns, roots, cons), details = asyncio.run(_all())
    return defns, roots, cons, details

# TODO update for response_format JSON
@traced
def extract_all(msg: str, bcp47: str, detail: bool=False) -> dict[str, dict]:
    """ Extract vocabulary terms from a message. This sequences a number of OpenAI API requests proportional to the number of vocab terms in the message. This is a convenience function that calls the other extract functions in this module.
    Args:
        msg (str): The message to extract vocabulary from.
        bcp47 (str): The BCP-47 language code of the message.
    """
    logger.warning("This function is not yet updated for response_format JSON. Expect high failure rate.")
    lang = Language(bcp47).name
    poss: dict[str, str] = extract_pos(msg)  # NOTE need to do this first because downstream completions are designed around separated terms
    logger.info(f"Extracted parts of speech: {poss}")
    terms = list(poss.keys())
    logger.info(f"Extracted terms: {terms}")
    verbs = list(set([term for term, pos in poss.items() if pos == "verb"]))
    logger.info(f"Extracted verbs: {verbs}")
    defns, roots, cons, details = _extract_all_async(terms, verbs, lang)
    logger.info(f"Extracted definitions: {defns}")
    logger.info(f"Extracted roots: {roots}")
    logger.info(f"Extracted verbs' conjugations: {cons}")
    result = {}
    for term in terms:
        result[term] = {
            'pos': poss.get(term),
            'defn': defns.get(term),
            'root': roots.get(term),
            'con': cons.get(term),
            'detail': details.get(term),
        }
    return result
