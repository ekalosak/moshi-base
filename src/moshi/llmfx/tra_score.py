from loguru import logger

from moshi import traced
from moshi.grade import Grade
from moshi.language import Language
from moshi.msg import Message
from moshi.prompt import Prompt
from moshi.transcript import Transcript

from .base import PROMPT_DIR

PROMPT_FILE = PROMPT_DIR / "tra_score_overall_grade.txt"
if not PROMPT_FILE.exists():
    raise FileNotFoundError(f"Prompt file {PROMPT_FILE} not found.")


@traced
def grade(tra: Transcript) -> Grade:
    """Grade the user's capabilities."""
    pro = Prompt.from_file(PROMPT_FILE)
    pro.template(GRADES=Grade.to_ranking())
    pro.msgs = tra.msgs + pro.msgs
    _gd = pro.complete().body.strip()
    gd = Grade.from_str(_gd)
    logger.success(f"Grade: {gd}")
    return gd