from pprint import pprint

from loguru import logger

from moshi import Message, Prompt, Vocab
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
    return vocs

def _extract_defn(vocs: list[Vocab], retry=1):
    """ Get the brief definitions of the vocab terms.
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
    return vocs


def _extract_detail(voc: Vocab) -> str:
    """ Get more information on the vocabulary term. """
    msgs = [
        Message('sys', f'Define the term "{voc.term}".'),
        Message('sys', f'Respond in {voc.bcp47}.'),
        Message('sys', f'Do not include "{voc.bcp47}" in the response.'),
    ]
    pro = Prompt(msgs=msgs)
    return pro.complete().body