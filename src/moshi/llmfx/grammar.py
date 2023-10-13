from loguru import logger

from moshi import Message, Prompt, traced
from .base import PROMPT_DIR

PROMPT_FILE = PROMPT_DIR / "grammar.txt"
if not PROMPT_FILE.exists():
    raise FileNotFoundError(f"Prompt file {PROMPT_FILE} not found.")

@traced
def explain(msg: str) -> str:
    """ Explain the grammar of a message. """
    pro = Prompt.from_file(PROMPT_FILE)
    pro.msgs.append(Message('usr', msg))
    logger.debug(f"Explaining grammar of message: {msg}")
    res = pro.complete().body
    logger.success(f"Explained grammar of message: {res}")
    return res