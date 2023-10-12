from pprint import pprint

from loguru import logger

from moshi import Prompt, Vocab
from .base import PROMPT_DIR

POS_PROMPT_FILE = PROMPT_DIR / "vocab_extract_pos.txt"
if not POS_PROMPT_FILE.exists():
    logger.warning(f"Prompt file {POS_PROMPT_FILE} not found.")

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