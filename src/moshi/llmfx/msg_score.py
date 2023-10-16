from loguru import logger

from moshi import Message, Prompt, traced
from moshi.language import Language
from moshi.vocab import MsgV
from .base import PROMPT_DIR

CONTEXT_PROMPT_FILE = PROMPT_DIR / "msg_score_context.txt"
GRAMMAR_PROMPT_FILE = PROMPT_DIR / "msg_score_grammar.txt"
IDIOMATICITY_PROMPT_FILE = PROMPT_DIR / "msg_score_idiomaticity.txt"
POLITENESS_PROMPT_FILE = PROMPT_DIR / "msg_score_politeness.txt"
VOCAB_PROMPT_FILE = PROMPT_DIR / "msg_score_vocab.txt"
PROMPT_FILES = [CONTEXT_PROMPT_FILE, GRAMMAR_PROMPT_FILE, IDIOMATICITY_PROMPT_FILE, POLITENESS_PROMPT_FILE, VOCAB_PROMPT_FILE]
for pf in PROMPT_FILES:
    if not pf.exists():
        raise FileNotFoundError(f"Prompt file {pf} not found.")

class ScoreParseError(Exception):
    """ Raised when a score cannot be parsed. """
    pass

@traced
def score_vocab(msg: str) -> float:
    """ Score the user's use of vocabulary in an utterance, from 1 to 10 inclusive.
    """
    pro = Prompt.from_file(VOCAB_PROMPT_FILE)
    msg = Message('usr', msg)
    pro.msgs.append(msg)
    logger.debug(f"Getting vocab score for: {msg}")
    _vsco = pro.complete().body
    logger.debug(f"Got vocab score: {_vsco}")
    try:
        vsco = float(_vsco.strip())
    except ValueError as exc:
        raise ScoreParseError(f"Failed to parse score: {_vsco}") from exc
    return vsco