from loguru import logger
from moshi.activ import Plan, pid2plan
from moshi.llmfx.base import PROMPT_DIR
from moshi.msg import Message
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
    pro.template(TRANSCRIPT=tra.to_templatable())
    topics: list[str] = pro.complete(stop=None).body.split(", ")
    logger.success(f"Extracted topics: {topics}")
    return topics