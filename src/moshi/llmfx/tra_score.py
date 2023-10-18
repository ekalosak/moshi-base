from loguru import logger

from moshi import traced
from moshi.grade import Grade
from moshi.language import Language
from moshi.msg import Message
from moshi.prompt import Prompt
from moshi.transcript import Transcript

from .base import PROMPT_DIR

GRADE_PROMPT_FILE = PROMPT_DIR / "tra_score_overall_grade.txt"
STRENGTH_PROMPT_FILE = PROMPT_DIR / "tra_score_strengths.txt"
WEAKNESS_PROMPT_FILE = PROMPT_DIR / "tra_score_weaknesses.txt"
for pf in [GRADE_PROMPT_FILE, STRENGTH_PROMPT_FILE, WEAKNESS_PROMPT_FILE]:
    if not pf.exists():
        raise FileNotFoundError(f"Prompt file {pf} not found.")

@traced
def grade(tra: Transcript) -> Grade:
    """Grade the user's overall capabilities."""
    pro = Prompt.from_file(GRADE_PROMPT_FILE)
    pro.template(GRADES=Grade.to_ranking())
    pro.msgs = tra.msgs + pro.msgs
    _gd = pro.complete(best_of=3).body.strip()
    gd = Grade.from_str(_gd)
    logger.success(f"Grade: {gd}")
    return gd

@traced
def strengths(tra: Transcript) -> str:
    """Assess the user's strengths."""
    # TODO FUTURE provide user name and ast char name to prompt
    if not tra.messages:
        return ''
    pro = Prompt.from_file(STRENGTH_PROMPT_FILE)
    pro.template(
        LANGUAGE=Language(tra.bcp47).name,
    )
    pro.msgs = pro.msgs[:-4] + tra.msgs + pro.msgs[-4:]
    st = pro.complete(presence_penalty=-0.8).body.strip()
    logger.success(f"Strengths: {st}")
    return st

@traced
def weakenesses(tra: Transcript) -> str:
    """Assess user's weaknesses."""
    if not tra.messages:
        return ''
    pro = Prompt.from_file(WEAKNESS_PROMPT_FILE)
    pro.template(
        LANGUAGE=Language(tra.bcp47).name,
    )
    pro.msgs = pro.msgs[:-1] + tra.msgs + pro.msgs[-1:]
    wk = pro.complete(best_of=3).body.strip()
    logger.success(f"Weaknesses: {wk}")
    return wk
