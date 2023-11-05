""" Extract topics from a transcript.
Constants:
    PROMPT_FILE: Path = PROMPT_DIR / "topics_extract.txt"
Functions:
    extract(tra: Transcript) -> list[str]
"""
from loguru import logger

from moshi.language import Language
from moshi.llmfx.base import PROMPT_DIR
from moshi.msg import message
from moshi.prompt import Prompt
from moshi.transcript import Transcript
from moshi import traced


PROMPT_FILE = PROMPT_DIR / "topics_extract.txt"
if not PROMPT_FILE.exists():
    raise FileNotFoundError(f"Prompt file {PROMPT_FILE} not found.")


@traced
def extract(tra: Transcript) -> list[str]:
    """Get a list of topics for the given transcript."""
    pro = Prompt.from_file(PROMPT_FILE)
    txt = '"""\n' + tra.to_templatable() + '\n"""'
    pro.template(
        LANGUAGE=Language(tra.bcp47).name,
        MAX_RESPONSES='five',
    )
    pro.msgs.append(message('usr', txt))
    topics: list[str] = pro.complete().body.split(", ")
    logger.success(f"Extracted topics: {topics}")
    return topics