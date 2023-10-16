from loguru import logger

from moshi import Message, Prompt, traced, Level
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

@traced
def score_grammar(msg: str) -> tuple[Level, str]:
    """ Score the user's use of grammar in an utterance, from 1 to 10 inclusive.
    """
    pro = Prompt.from_file(GRAMMAR_PROMPT_FILE)
    pro.template(RANKING=Level.to_ranking())
    msg = Message('usr', msg)
    pro.msgs.append(msg)
    logger.debug(f"Getting grammar score for: {msg}")
    _gsco = pro.complete().body
    logger.debug(f"Got grammar score: {_gsco}")
    try:
        gsco, expl = _gsco.split('; ')
        expl = expl.strip()
        gsco = Level.from_str(gsco.strip())
    except ValueError as exc:
        raise ScoreParseError(f"Failed to parse score: {_gsco}") from exc
    return gsco, expl

@traced
def score_polite(msg: str) -> tuple[float, str]:
    """ Score the user's utterance for politeness, from 1 to 10 inclusive.
    """
    pro = Prompt.from_file(POLITENESS_PROMPT_FILE)
    msg = Message('usr', msg)
    pro.msgs.append(msg)
    logger.debug(f"Getting politeness score for: {msg}")
    _psco = pro.complete().body
    logger.debug(f"Got politeness score: {_psco}")
    try:
        psco, expl = _psco.split('; ')
        expl = expl.strip()
        psco = float(psco.strip())
    except ValueError as exc:
        raise ScoreParseError(f"Failed to parse score: {_psco}") from exc
    return psco, expl

@traced
def score_idiomaticity(msg: str) -> tuple[float, str]:
    """ Score the user's utterance for idiomaticity, from 1 to 10 inclusive.
    """
    pro = Prompt.from_file(IDIOMATICITY_PROMPT_FILE)
    msg = Message('usr', msg)
    pro.msgs.append(msg)
    logger.debug(f"Getting politeness score for: {msg}")
    _isco = pro.complete().body
    logger.debug(f"Got idiomaticity score: {_isco}")
    try:
        isco, expl = _isco.split('; ')
        expl = expl.strip()
        isco = float(isco.strip())
    except ValueError as exc:
        raise ScoreParseError(f"Failed to parse score: {_isco}") from exc
    return isco, expl