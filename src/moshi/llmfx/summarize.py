from pathlib import Path

from loguru import logger

from moshi.msg import Message
from moshi.prompt import Prompt

PROMPT_DIR = Path(__file__).parent / "prompts"
PROMPT_FILE = PROMPT_DIR / "summarize.txt"

def _base_prompt() -> Prompt:
    return Prompt.from_file(PROMPT_FILE)

def summarize(msgs: list[Message], nwords: int=5, bcp47: str="en-US") -> str:
        msgs = sorted(msgs, key=lambda msg: msg.created_at)
        pro = _base_prompt()
        pro.msgs = msgs + pro.msgs
        pro.template(NWORDS=nwords)
        pro.translate(bcp47=bcp47)
        return pro.complete().body