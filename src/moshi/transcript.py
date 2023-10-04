from datetime import datetime

from google.cloud import firestore
from loguru import logger
from pydantic import Field

from .activ import ActT, Plan
from .log import traced
from .msg import Message
from .storage import FB, DocPath
from .utils import id_prefix

def _a2int(audio_name: str) -> int:
    """Convert an audio name to an integer."""
    with logger.contextualize(audio_name=audio_name):
        fn = audio_name.split('/')[-1]
        return int(fn.split('-')[0])

def _transcript_id(bcp47: str) -> str:
    """ Generate a unique ID for a transcript. """
    return f"{id_prefix()}-{bcp47}"

class Transcript(FB):
    aid: str = Field(help='Activity ID.')
    atp: ActT = Field(help='Activity type.')
    pid: str = Field(help='Plan ID.')
    tid: str = Field(help='Transcript ID.', default_factory=_transcript_id)
    uid: str = Field(help='User ID.')
    bcp47: str = Field(help='User language e.g. "en-US".')
    messages: list[Message] = Field(help='Content of the conversation.')

    @property
    def docpath(self) -> DocPath:
        return DocPath(f'users/{self.uid}/transcripts/{self.tid}')

    @classmethod
    def from_plan(cls, plan: Plan) -> 'Transcript':
        return cls(
            aid=plan.aid,
            atp=plan.atp,
            pid=plan.pid,
            uid=plan.uid,
            bcp47=plan.bcp47,
            messages=[],
        )

    @classmethod
    def _kwargs_from_docpath(cls, docpath: DocPath) -> dict:
        """ Get kwargs from the docpath. For example, /users/<uid> should return {'uid': <uid>}. """
        if len(docpath.parts) != 4:
            raise ValueError(f"Invalid docpath for plan, must have 4 parts: {docpath}")
        if docpath.parts[0] != 'users':
            raise ValueError(f"Invalid docpath for plan, first part must be 'users': {docpath}")
        if docpath.parts[2] != 'transcripts':
            raise ValueError(f"Invalid docpath for plan, third part must be 'transcripts': {docpath}")
        return {
            'uid': docpath.parts[1],
            'tid': docpath.parts[3],
        }

    def to_json(self, *args, exclude=['tid', 'uid'], **kwargs) -> dict:
        return super().to_json(*args, exclude=exclude, **kwargs)

    def add_msg(self, msg: Message) -> None:
        """Add a message to the transcript."""
        self.messages.append(msg)