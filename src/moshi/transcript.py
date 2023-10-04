from datetime import datetime

from google.cloud import firestore
from loguru import logger
from pydantic import Field

from .activ import ActT
from .log import traced
from .msg import Message
from .storage import FB

def _a2int(audio_name: str) -> int:
    """Convert an audio name to an integer."""
    with logger.contextualize(audio_name=audio_name):
        fn = audio_name.split('/')[-1]
        return int(fn.split('-')[0])

class Transcript(FB):
    aid: str = Field(help='Activity ID.')
    aty: ActT = Field(help='Activity type.')
    pid: str = Field(help='Plan ID.')
    tid: str = Field(help='Transcript ID.')
    uid: str = Field(help='User ID.')
    bcp47: str = Field(help='User language e.g. "en-US".')
    messages: list[Message] = Field(help='Content of the conversation.')

    def add_msg(self, msg: Message) -> None:
        """Add a message to the transcript."""
        self.messages.append(msg)