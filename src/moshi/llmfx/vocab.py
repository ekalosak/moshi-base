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

from moshi import Message, Prompt, Vocab, traced
from .base import PROMPT_DIR

POS_PROMPT_FILE = PROMPT_DIR / "vocab_extract_pos.txt"
DEFN_PROMPT_FILE = PROMPT_DIR / "vocab_extract_defn.txt"
ROOT_PROMPT_FILE = PROMPT_DIR / "vocab_extract_verb_root.txt"
CONJ_PROMPT_FILE = PROMPT_DIR / "vocab_extract_verb_conjugation.txt"
PROMPT_FILES = [POS_PROMPT_FILE, DEFN_PROMPT_FILE, ROOT_PROMPT_FILE, CONJ_PROMPT_FILE]
for pf in PROMPT_FILES:
    if not pf.exists():
        raise FileNotFoundError(f"Prompt file {pf} not found.")

class VocabParseError(Exception):
    """ Raised when a vocabulary term cannot be parsed. """
    pass

@traced
def _extract_pos(msg: str, retry=3) -> list[Vocab]:
    """ Get the parts of speech of the vocab terms of a message.
    Args:
        msg (str): The message to extract vocabulary from.
    """
    pro = Prompt.from_file(POS_PROMPT_FILE)
    pro.template(UTT=msg)
    for msg in pro.msgs:
        print(msg)
    _vocs = pro.complete(stop=None).body.split("\n")
    vocs = []
    try:
        for v in _vocs:
            try:
                term, pos = v.split(";")
            except ValueError as exc:
                raise VocabParseError(f"Failed to parse vocabulary term: {v}") from exc
            else:
                vocs.append(Vocab(term=term.strip(), pos=pos.strip()))
    except VocabParseError as exc:
        if retry > 0:
            logger.warning(exc)
            logger.debug(f"Retrying with {retry-1} retries left.")
            return _extract_pos(msg, retry=retry-1)
        else:
            raise exc
    logger.success(f"Extracted parts of speech: {vocs}")
    return vocs

@traced
def _extract_defn(vocs: list[Vocab], retry=3):
    """ Get the brief definitions of the vocab terms. Modifies the vocs in place.
    Args:
        vocs (list[Vocab]): The vocabulary terms to get definitions for.
    """
    pro = Prompt.from_file(DEFN_PROMPT_FILE)
    vocs_commmasep: str = ", ".join([v.term for v in vocs])
    pro.msgs.append(Message('usr', vocs_commmasep))
    pro.template(LANGNAME=vocs[0].lang.name)
    _vocs = pro.complete(stop=None).body.split("\n")
    vocd = {v.term: v for v in vocs}
    try:
        if len(_vocs) != len(vocs):
            raise VocabParseError(f"Completion returned different number of terms: {vocs_commmasep} -> {_vocs}")
        for v in _vocs:
            try:
                term, defn = v.split(";")
            except ValueError as exc:
                raise VocabParseError(f"Failed to parse vocabulary term: {v}") from exc
            else:
                voc = vocd[term.strip()]
                voc.defn = defn.strip()
    except VocabParseError as exc:
        if retry > 0:
            logger.warning(exc)
            logger.debug(f"Retrying with {retry-1} retries left.")
            return _extract_defn(vocs, retry=retry-1)
        else:
            raise exc
    logger.success(f"Extracted definitions: {vocs}")


@traced
def _extract_detail(voc: Vocab):
    """ Get more information on the vocabulary term. Modifies the voc in place. """
    msgs = [
        Message('sys', f'Define the term "{voc.term}".'),
        Message('sys', f'Respond in {voc.lang}.'),
    ]
    pro = Prompt(msgs=msgs)
    voc.detail = pro.complete().body
    logger.success(f"Extracted detail: {voc}")

@traced
def _extract_verb_root(vocs: list[Vocab]):
    """ Get the root forms of verbs. Modifies the vocs in place. """
    pro = Prompt.from_file(ROOT_PROMPT_FILE)
    verbs = [v for v in vocs if v.pos == "verb"]  # NOTE this copies the Vocab objects
    if not verbs:
        logger.debug("No verbs found.")
        return
    msg = Message('usr', "; ".join([v.term for v in verbs]))
    pro.msgs.append(msg)
    _vocs = pro.complete().body.split("; ")
    if len(_vocs) != len(verbs):
        raise VocabParseError(f"Completion returned different number of terms: {verbs} -> {_vocs}")
    for verb, root in zip(verbs, _vocs):
        verb.root = root
    logger.success(f"Extracted verb roots: {verbs}")


@traced
def _extract_verb_conjugation(vocs: list[Vocab]):
    """ Get the conjugations of verbs. Modifies the vocs in place. """
    pro = Prompt.from_file(CONJ_PROMPT_FILE)
    verbs = [v for v in vocs if v.pos == "verb"]
    if not verbs:
        logger.debug("No verbs found.")
        return
    msg = Message('usr', "; ".join([v.term for v in verbs]))
    pro.msgs.append(msg)
    _vocs = pro.complete().body.split("; ")
    if len(_vocs) != len(verbs):
        raise VocabParseError(f"Completion returned different number of terms: {verbs} -> {_vocs}")
    for verb, con in zip(verbs, _vocs):
        verb.conju = con
    logger.success(f"Extracted verb conjugations: {verbs}")

@traced
def extract(msg: str, bcp47: str, detail: bool=False) -> list[Vocab]:
    """ Extract vocabulary terms from a message. This is the main entrypoint. It calls all the other functions in this module, each of which is responsible for extracting a different piece of information via OpenAI's API. As such, this function may take a while to run and should not be called as a blocking part of the session.
    Args:
        msg (str): The message to extract vocabulary from.
        bcp47 (str): The BCP-47 language code of the message.
    """
    vocs = _extract_pos(msg)
    for voc in vocs:
        voc.bcp47 = bcp47
    _extract_defn(vocs)
    _extract_verb_root(vocs)
    _extract_verb_conjugation(vocs)
    if detail:
        for voc in vocs:
            _extract_detail(voc)
    return vocs