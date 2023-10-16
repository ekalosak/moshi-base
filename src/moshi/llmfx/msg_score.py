from loguru import logger
from zipp import Path

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
def _score(msg: str, pro: Path | Prompt, **kwargs) -> tuple[Level, str]:
    """ Score a message using a prompt file.
    """
    if isinstance(pro, Path):
        pro = Prompt.from_file(pro)
    assert 'RANKING' not in kwargs
    pro.template(RANKING=Level.to_ranking())
    if kwargs:
        pro.template(**kwargs)
    msg = Message('usr', msg)
    pro.msgs.append(msg)
    logger.debug(f"Getting score for: {msg}")
    _sco = pro.complete().body
    logger.debug(f"Got score: {_sco}")
    try:
        sco, expl = _sco.split('; ')
        expl = expl.strip()
        sco = Level.from_str(sco.strip())
    except ValueError as exc:
        raise ScoreParseError(f"Failed to parse score: {_sco}") from exc
    return sco, expl

@traced
def score_vocab(msg: str) -> tuple[Level, str]:
    """ Score the user's use of vocabulary in an utterance.
    """
    return _score(msg, VOCAB_PROMPT_FILE)

@traced
def score_grammar(msg: str) -> tuple[Level, str]:
    """ Score the user's use of grammar in an utterance.
    """
    return _score(msg, GRAMMAR_PROMPT_FILE)

@traced
def score_polite(msg: str) -> tuple[float, str]:
    """ Score the user's utterance for politeness.
    """
    return _score(msg, POLITENESS_PROMPT_FILE)

@traced
def score_idiomaticity(msg: str) -> tuple[float, str]:
    """ Score the user's utterance for idiomaticity.
    """
    return _score(msg, IDIOMATICITY_PROMPT_FILE)

@traced
def score_context(msgs: list[str]) -> tuple[Level, str]:
    """ Score the user's utterance for context.
    Scores 
    """
    pld = ""
    for speaker, msg in enumerate(msgs):
        speaker = speaker % 2 + 1
        pld += f"{speaker}: {msg}\n"
    return _score(msg, CONTEXT_PROMPT_FILE)