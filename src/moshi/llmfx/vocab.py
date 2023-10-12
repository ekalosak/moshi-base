from loguru import logger

from moshi import Message, Prompt, Vocab
from .base import PROMPT_DIR

POS_PROMPT_FILE = PROMPT_DIR / "vocab_extract_pos.txt"
if not POS_PROMPT_FILE.exists():
    logger.warning(f"Prompt file {POS_PROMPT_FILE} not found.")

def extract(msg: str) -> list[Vocab]:
    """ Get the vocabulary terms from the message. """
    pro = Prompt.from_file(POS_PROMPT_FILE)
    pro.template(UTT=msg)
    _vocs = pro.complete().body.split("\n")
    vocs = []
    for v in _vocs:
        term, pos = v.split(";")
        vocs.append(Vocab(term=term.strip(), part_of_speech=pos.strip()))
    return vocs