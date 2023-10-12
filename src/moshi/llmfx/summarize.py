from pathlib import Path

from loguru import logger

from moshi.language import Language
from moshi.msg import Message
from moshi.prompt import Prompt
from moshi.transcript import Transcript

PROMPT_DIR = Path(__file__).parent / "prompts"
PROMPT_FILE = PROMPT_DIR / "summarize.txt"

def _base_prompt() -> Prompt:
    return Prompt.from_file(PROMPT_FILE)

def summarize(tra: Transcript, nwords: int, summary_language: Language) -> str:
        tra.messages: list[Message]
        msgs = sorted(tra.messages, key=lambda msg: msg.created_at)
        pro = _base_prompt()
        pro.msgs = msgs + pro.msgs
        pro.template(NWORDS=5)
        return pro.complete().body