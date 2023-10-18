from loguru import logger

from moshi import traced
from moshi.grade import Grade
from moshi.language import Language
from moshi.msg import Message
from moshi.prompt import Prompt
from moshi.transcript import Transcript

from .base import PROMPT_DIR

GRADE_PROMPT_FILE = PROMPT_DIR / "tra_score_overall_grade.txt"
SKILLS_PROMPT_FILE = PROMPT_DIR / "tra_score_skill_assessment.txt"
SPLIT_PROMPT_FILE = PROMPT_DIR / "tra_score_split_skills.txt"
for pf in [GRADE_PROMPT_FILE, SKILLS_PROMPT_FILE, SPLIT_PROMPT_FILE]:
    if not pf.exists():
        raise FileNotFoundError(f"Prompt file {pf} not found.")

@traced
def grade(tra: Transcript) -> Grade:
    """Grade the user's overall capabilities."""
    if not tra.messages or len(tra.messages) < 3:
        logger.debug(f"Transcript has {len(tra.messages)} < 3 messages, skipping grading.")
        return ''
    pro = Prompt.from_file(GRADE_PROMPT_FILE)
    pro.template(GRADES=Grade.to_ranking())
    pro.msgs = tra.msgs + pro.msgs
    _gd = pro.complete(presence_penalty=-1.0).body.strip()
    gd = Grade.from_str(_gd)
    logger.success(f"Grade: {gd}")
    return gd

@traced
def split_into_str_and_weak(skill_summary: str) -> tuple[str, str]:
    """Split the skill summary into strengths and weaknesses."""
    if not skill_summary:
        return ''
    pro = Prompt.from_file(SPLIT_PROMPT_FILE)
    pro.msgs = pro.msgs + [Message('usr', skill_summary)]
    res = pro.complete(presence_penalty=-2.0, stop=['\n\n']).body.strip()
    logger.success(f"Split skills into strengths and weaknesses: {res}")
    st, wk = res.split('\n')
    return st, wk

@traced
def summarize_skills(tra: Transcript) -> str:
    """Assess the user's strengths and weaknesses."""
    # TODO FUTURE provide user name and ast char name to prompt
    if not tra.messages or len(tra.messages) < 3:
        logger.debug(f"Transcript has {len(tra.messages)} < 3 messages, skipping skill assessment.")
        return ''
    pro = Prompt.from_file(SKILLS_PROMPT_FILE)
    pro.template(
        LANGUAGE=Language(tra.bcp47).name,
    )
    pro.msgs = pro.msgs[:-4] + tra.msgs + pro.msgs[-4:]
    skill_summary = pro.complete(presence_penalty=-0.8).body.strip()
    logger.success(f"Skill summary: {skill_summary}")
    return skill_summary