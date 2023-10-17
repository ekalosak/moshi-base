"""
The `summarize` module provides a function for summarizing a conversation in natural language.

Example usage:

    >>> from moshi.msg import Message
    >>> from summarize import summarize
    >>> msgs = [
    ...     Message(body="Hello!", sender="Alice", created_at=0),
    ...     Message(body="Hi there!", sender="Bob", created_at=1),
    ...     Message(body="How are you?", sender="Alice", created_at=2),
    ...     Message(body="I'm good, thanks. How about you?", sender="Bob", created_at=3),
    ...     Message(body="I'm doing well too, thanks for asking.", sender="Alice", created_at=4),
    ... ]
    >>> summary = summarize(msgs, nwords=5)
    >>> print(summary)
    "Alice and Bob exchanged greetings."

"""
from loguru import logger

from moshi.log import traced
from moshi.msg import Message
from moshi.prompt import Prompt
from .base import PROMPT_DIR

PROMPT_FILE = PROMPT_DIR / "summarize.txt"

@traced
def summarize(msgs: list[Message], nwords: int=5, bcp47: str="en-US") -> str:
    """ Summarize a list of messages. """
    msgs = sorted(msgs, key=lambda msg: msg.created_at)
    pro = Prompt.from_file(PROMPT_FILE)
    pro.msgs = msgs + pro.msgs
    pro.template(NWORDS=nwords)
    logger.warning("TRANSLATING PROMPT UNCACHED")
    pro.translate(bcp47=bcp47)
    return pro.complete().body