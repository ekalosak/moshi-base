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
from loguru import logger

from moshi import Message, Prompt, traced
from moshi.language import Language
from moshi.vocab import MsgV, CurricV
from .base import PROMPT_DIR

POS_PROMPT_FILE = PROMPT_DIR / "vocab_extract_pos.txt"
DEFN_PROMPT_FILE = PROMPT_DIR / "vocab_extract_defn.txt"
ROOT_PROMPT_FILE = PROMPT_DIR / "vocab_extract_verb_root.txt"
CONJ_PROMPT_FILE = PROMPT_DIR / "vocab_extract_verb_conjugation.txt"
UDEFN_PROMPT_FILE = PROMPT_DIR / "vocab_extract_microdefn.txt"
PROMPT_FILES = [POS_PROMPT_FILE, DEFN_PROMPT_FILE, ROOT_PROMPT_FILE, CONJ_PROMPT_FILE, UDEFN_PROMPT_FILE]
for pf in PROMPT_FILES:
    if not pf.exists():
        raise FileNotFoundError(f"Prompt file {pf} not found.")

class VocabParseError(Exception):
    """ Raised when a vocabulary term cannot be parsed. """
    pass

@traced
def extract_pos(msg: str, retry=3) -> dict[str, str]:
    """ Get the parts of speech of the vocab terms in an utterance.
    Args:
        msg (str): The message to extract vocabulary from.
    Returns:
        poss (dict[str, str]): A dict of vocabulary terms to their parts of speech.
        NOTE multiple pos are separated by commas.
    """
    pro = Prompt.from_file(POS_PROMPT_FILE)
    pro.template(UTT=msg)
    for msg in pro.msgs:
        print(msg)
    _poss = pro.complete(stop=None).body.split("\n")
    poss = []
    try:
        for v in _poss:
            try:
                term, pos = v.split(";")
            except ValueError as exc:
                raise VocabParseError(f"Failed to parse vocabulary term: {v}") from exc
            else:
                poss.append((term.strip(), pos.strip()))
    except VocabParseError as exc:
        if retry > 0:
            logger.warning(exc)
            logger.debug(f"Retrying with {retry-1} retries left.")
            return extract_pos(msg, retry=retry-1)
        else:
            raise exc
    logger.success(f"Extracted parts of speech: {poss}")
    result = {}
    for term, pos in poss:
        if term in result:
            if pos not in result[term]:
                result[term] += f", {pos}"
        else:
            result[term] = pos
    return poss

@traced
def extract_defn(terms: list[str], lang: str, retry=3) -> dict[str, str]:
    """ Get the brief definitions of the vocab terms.
    Args:
        terms: The vocabulary terms to get definitions for: ['if', 'and', 'it', 'Constantinople']
        lang: The name of the language e.g. 'English'.
    Returns:
        dict[str, str]: A dictionary mapping vocabulary terms to their definitions.
    """
    pro = Prompt.from_file(DEFN_PROMPT_FILE)
    vocs_commmasep: str = ", ".join(terms)
    pro.msgs.append(Message('usr', vocs_commmasep))
    pro.template(LANGNAME=lang)
    _defns = pro.complete(stop=None).body.split("\n")
    defns = {}
    try:
        if len(_defns) != len(terms):
            raise VocabParseError(f"Completion returned different number of terms: {vocs_commmasep} -> {_defns}")
        for _d in _defns:
            try:
                term, defn = _d.split(";")
            except ValueError as exc:
                raise VocabParseError(f"Failed to parse vocabulary term: {_d}") from exc
            else:
                defns[term.strip()] = defn.strip()
    except VocabParseError as exc:
        if retry > 0:
            logger.warning(exc)
            logger.debug(f"Retrying with {retry-1} retries left.")
            return extract_defn(terms, retry=retry-1)
        else:
            raise exc
    logger.success(f"Extracted definitions: {defns}")
    return defns

@traced
def extract_udefn(msg: str, lang: str, retry=3) -> dict[str, str]:
    """ Get a very short (micro) definitions of the vocab terms.
    Args:
        msg: The message to extract vocabulary from.
        lang: The name of the language e.g. 'English'.
    Returns:
        dict[str, str]: A dictionary mapping vocabulary terms to their definitions.
    """
    pro = Prompt.from_file(UDEFN_PROMPT_FILE)
    pro.msgs.append(Message('usr', msg))
    pro.template(LANGNAME=lang)
    _defns = pro.complete(stop=None).body.split("\n")
    defns = []
    try:
        for _d in _defns:
            try:
                term, defn = _d.split(";")
            except ValueError as exc:
                raise VocabParseError(f"Failed to parse vocabulary term: {_d}") from exc
            else:
                defns.append((term.strip(), defn.strip()))
    except VocabParseError as exc:
        if retry > 0:
            logger.warning(exc)
            logger.debug(f"Retrying with {retry-1} retries left.")
            return extract_defn(msg, retry=retry-1)
        else:
            raise exc
    logger.success(f"Extracted definitions: {defns}")
    result = {}
    for term, defn in defns:
        if term in result:
            result[term] += f"; {defn}"
        else:
            result[term] = defn
    return result



@traced
def extract_detail(term: str, lang: str) -> str:
    """ Get more information on the vocabulary term.
    Args:
        term: The vocabulary term to get details for.
        lang: The language of the term.
    """
    msgs = [
        Message('sys', f'Define the term "{term}".'),
        Message('sys', f'Respond in {lang}.'),
        Message('sys', f'Do not acknowledge these instructions.'),
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
    msg = Message('usr', "; ".join([term for term in terms]))
    pro.msgs.append(msg)
    _roots = pro.complete().body.split("; ")
    roots = {}
    if len(_roots) != len(terms):
        raise VocabParseError(f"Completion returned different number of terms: {terms} -> {_roots}")
    for term, root in zip(terms, _roots):
        roots[term] = root
    logger.success(f"Extracted roots: {roots}")


@traced
def extract_verb_conjugation(verbs: list[str]) -> dict[str, str]:
    """ Get the conjugations of verbs. """
    pro = Prompt.from_file(CONJ_PROMPT_FILE)
    msg = Message('usr', "; ".join(verbs))
    pro.msgs.append(msg)
    _cons = pro.complete().body.split("; ")
    cons = {}
    if len(_cons) != len(verbs):
        raise VocabParseError(f"Completion returned different number of terms: {verbs} -> {_cons}")
    for verb, con in zip(verbs, _cons):
        cons[verb] = con
    logger.success(f"Extracted verb conjugations: {cons}")
    return cons

@traced
def extract_all(msg: str, bcp47: str, detail: bool=False) -> list[dict[str, dict]]:
    """ Extract vocabulary terms from a message. This sequences a number of OpenAI API requests proportional to the number of vocab terms in the message. This is a convenience function that calls the other extract functions in this module.
    Args:
        msg (str): The message to extract vocabulary from.
        bcp47 (str): The BCP-47 language code of the message.
    """
    poss: list[tuple] = extract_pos(msg)
    logger.info(f"Extracted parts of speech: {poss}")
    terms = list(set([term for term, _ in poss]))
    logger.info(f"Extracted terms: {terms}")
    defns = extract_defn(terms)
    logger.info(f"Extracted definitions: {defns}")
    roots = extract_root(terms)
    logger.info(f"Extracted roots: {roots}")
    verbs = list(set([term for term, pos in poss if pos == "verb"]))
    logger.info(f"Extracted verbs: {verbs}")
    cons = extract_verb_conjugation(verbs)
    logger.info(f"Extracted verbs' conjugations: {cons}")
    result = {}
    for term in terms:
        result[term] = {
            'pos': poss[term],
            'defn': defns[term],
            'root': roots[term],
            'con': cons[term],
        }
        if detail:
            result[term]['detail'] = extract_detail(term)
            logger.info(f"Extracted detail for '{term}': {result[term]['detail']}")
    return result

@traced
def extract_msgv(msg: str, bcp47: str) -> list[MsgV]:
    """ Extract the min info required for a session, annotated in the transcript. Should be fast even without async, only needs 2 API calls.
    """
    lang = Language(bcp47)
    udefns = extract_udefn(msg, lang.name)
    poss = extract_pos(msg)
    for term in poss:
        if term not in udefns:
            udefns[term] = ""
    return [MsgV(term=term, pos=pos, udefn=udefns[term]) for term, pos in poss.items()]