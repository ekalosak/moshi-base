from pathlib import Path

from loguru import logger
from typing import TypeVar

from moshi import Message, Prompt, traced
from moshi.exceptions import ScoreParseError
from moshi.grade import Rankable, YesNo, Level, Score
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

@traced
def _score(msg: str, pro: Path | Prompt, score_as: Rankable=Level, **kwargs) -> Score:
    """ Score a message using a prompt file.
    Args:
        msg: The message to score.
        pro: The prompt file or prompt to use.
        score_as: The type of score to return.
        **kwargs: The keyword arguments to pass to the prompt as template variables.
            The RANKING variable is automatically set to the ranking of the score type (e.g. Level.to_ranking()).
    """
    if isinstance(pro, Path):
        logger.debug(f"Loading prompt from file: {pro}")
        pro = Prompt.from_file(pro)
    assert 'RANKING' not in kwargs
    pro.template(RANKING=score_as.to_ranking())
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
        sco = score_as.from_str(sco.strip())
    except ValueError as exc:
        raise ScoreParseError(f"Failed to parse score: {_sco}") from exc
    return Score(sco, expl)

@traced
def score_vocab(msg: str) -> Score:
    """ Score the user's use of vocabulary in an utterance.
    """
    return _score(msg, VOCAB_PROMPT_FILE)

@traced
def score_grammar(msg: str) -> Score:
    """ Score the user's use of grammar in an utterance.
    """
    return _score(msg, GRAMMAR_PROMPT_FILE)

@traced
def score_polite(msg: str) -> Score:
    """ Score the user's utterance for politeness.
    """
    return _score(msg, POLITENESS_PROMPT_FILE, score_as=YesNo)

@traced
def score_idiom(msg: str) -> Score:
    """ Score the user's utterance for idiomaticity.
    """
    return _score(msg, IDIOMATICITY_PROMPT_FILE, score_as=YesNo)

@traced
def score_context(msgs: list[Message]) ->  Score:
    """ Score the user's utterance for context.
    """
    pld = ""
    for msg in msgs:
        pld += f"{msg.role.name}: {msg.body}\n"
    pld.strip()
    return _score(pld, CONTEXT_PROMPT_FILE, score_as=YesNo)