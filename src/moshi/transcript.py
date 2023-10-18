""" The Transcript holds the live session state object.
It is stored in Firestore at /users/<uid>/transcripts/<tid>.
In comparison:
    - the Activity[T] (T bound by ActT) has the session state machine logic.
    - the Plan[T] (T bound by ActT) has the activity configuration.
Note that the Transcript is generic across ActT.

When a session is 'live', the Transcript is stored in Firestore at: /users/<uid>/live/<tid>
In this state, the messages are stored in subcollections:
    - /users/<uid>/live/<tid>/amsgs
    - /users/<uid>/live/<tid>/umsgs
This complexity allows different message types to trigger different Functions, and different functionality is indeed required for different message roles in a session.

After the session terminates, the umsgs and amsgs are merged into the Transcript document
    under the 'msgs' attribute, and the document is 'moved' (copied and deleted) to /users/<uid>/final/<tid>.
This complexity allows different enrichment functionality to be applied to the messages after the session terminates e.g. translation, summarization, subsequent lesson planning, etc. Moreover, it allows the avoidance of unnecessarily loading the live-session functionality when the session is not live and updates are made.
"""
from itertools import chain
from lib2to3.pgen2 import grammar
from typing import TypeVar

from google.cloud.firestore import Client, CollectionReference
from loguru import logger
from pydantic import BaseModel, Field, field_validator, ValidationInfo, computed_field

from .activ import ActT, Plan
from .grade import Grade, Score, Scores
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

class ScoreT(BaseModel):
    """ A single transcript's scores, aggregated into a median and MAD. """
    median: float
    mad: float

class ScoresT(BaseModel):
    vocab: ScoreT = None
    grammar: ScoreT = None
    idiom: ScoreT = None
    polite: ScoreT = None
    context: ScoreT = None

T = TypeVar('T', bound=[int, float])

def median(lst: list[T]) -> T:
    """ Return the median of a list of numeric values. """
    lst = sorted(lst)
    n = len(lst)
    if n % 2 == 0:
        return (lst[n//2] + lst[n//2 - 1]) / 2
    else:
        return lst[n//2]

class Transcript(FB):
    messages: list[Message] = None
    aid: str = Field(help='Activity ID.')
    atp: ActT = Field(help='Activity type.')
    pid: str = Field(help='Plan ID.')
    uid: str = Field(help='User ID.')
    bcp47: str = Field(help='User language e.g. "en-US".')
    tid: str = Field(None, help='Transcript ID. One is created if not provided.', validate_default=True)
    summary: str = None
    grade: Grade=Field(None, help='Overall grade. Created upon finalization.')
    topics: list[str]=Field(None, help='Topic tags. Created upon finalization.')
    strengths: list[str]=Field(None, help='User strengths across all messages. Created upon finalization.')
    focus: list[str]=Field(None, help='User weaknesses across all messages. Created upon finalization.')
    status: str = Field('live', help='Transcript status. One of "live", "final".')

    @property
    def msgs(self):
        return self.messages

    def to_templatable(self, roles=['ast', 'usr']) -> str:
        """ Convert the transcript to a string that can be used in a template.
        Args:
            roles: those roles to include in the template.
        Example return value:
        ```
        ast: hello
        usr: hi
        ```
        """
        if not self.messages:
            return ''
        mstrs: list[str] = []
        for msg in self.msgs:
            if msg.role.value.lower() not in roles:
                continue
            mstrs.append(f"{msg.role.value.lower()}: {msg.body.strip()}")
        return "\n".join(mstrs).strip()

    @computed_field
    @property
    def scores(self) -> ScoresT | None:
        """ If there are enough messages, calculate overall VGIPC scores.
        The scores are a median and mad for each of VGIPC (vocab, grammar, idiom, polite, context).
        """
        if not self.messages:
            logger.debug("No messages in transcript, cannot compute scores.")
            return None
        elif (nmsg := len(self.messages)) < 4:
            logger.debug(f"Not enough messages (nmsg={nmsg} < 4) in transcript, cannot compute scores.")
            return None
        _all: dict[str, list[int]] = {}
        for msg in self.messages:
            if msg.role != 'usr':
                continue
            if scos := msg.score:
                for name, sco in scos.each:
                    if name not in _all:
                        _all[name] = []
                    _all[name].append(int(sco.score))
            else:
                logger.debug(f"Message {msg} has no score.")
        if not _all:
            logger.debug("No scores in transcript, cannot compute scores.")
            return None
        medians: dict[str, int] = {}
        mads: dict[str, float] = {}
        for name, vals in _all.items():
            if nscos := len(vals) < 4:
                logger.warning(f"Not enough scores (nscos={nscos} < 4) for {name} transcript, cannot compute scores.")
            else:
                medians[name] = median(vals)
                mads[name] = median([abs(val - medians[name]) for val in vals])
        scost_pld = {}
        for name in ('vocab', 'grammar', 'idiom', 'polite', 'context'):
            if name in medians:
                scost_pld[name] = ScoreT(median=medians[name], mad=mads[name])
        return ScoresT(**scost_pld)

    @field_validator('tid', mode='before')
    @classmethod
    def provide_tid(cls, v, values: ValidationInfo):
        if v is None:
            return _transcript_id(values.data['bcp47'])
        return v

    @field_validator('messages', mode='before')
    @classmethod
    def parse_msg_dict(cls, v: list[Message] | list[dict[str, str]] | dict[str, dict[str, str]] , values: ValidationInfo):
        if not v:
            return []
        if isinstance(v, dict):
            return [Message(**msg) for msg in v.values()]
        elif isinstance(v, list):
            if isinstance(v[0], dict):
                return [Message(**msg) for msg in v]
            else:
                return v
        else:
            raise ValueError(f"Invalid type for messages: {type(v)}")

    @classmethod
    def get_docpath(cls, uid, tid) -> DocPath:
        return DocPath(f'users/{uid}/transcripts/{tid}')

    @property
    def docpath(self) -> DocPath:
        return Transcript.get_docpath(self.uid, self.tid)

    @classmethod
    def from_plan(cls, plan: Plan) -> 'Transcript':
        return cls(
            aid=plan.aid,
            atp=plan.atp,
            pid=plan.pid,
            uid=plan.uid,
            bcp47=plan.bcp47,
        )

    @classmethod
    def from_ids(cls, uid, tid, db) -> 'Transcript':
        """ Get a transcript from Firestore. """
        docpath = cls.get_docpath(uid, tid)
        return cls.read(docpath, db)

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
        js = super().to_json(*args, exclude=exclude, **kwargs)
        if 'messages' in js:
            js['messages'] = {
                msg.role.value.upper() + str(i): msg.to_json()
                for i, msg in enumerate(self.messages)
            }
        return js

    def _send_msg_to_subcollection(self, msg: Message, msg_id: str, db: Client):
        """ Add a message to the appropriate subcollection.
        The only allowd roles are 'usr' and 'ast'.
        Returns:
            The message ID.
        """
        match msg.role:
            case 'usr':
                colnm = 'umsgs'
            case 'ast':
                colnm = 'amsgs'
            case _:
                raise ValueError(f"Invalid role, only 'ast' and 'usr' are valid in transcript, got: {msg.role}")
        with logger.contextualize(collection_name=colnm):
            logger.debug(f"Adding message to transcript: {msg}")
        col: CollectionReference = self.docref(db).collection(colnm)
        with logger.contextualize(msg_id=msg_id):
            logger.debug(f"Adding message to transcript...")
            col.document(msg_id).set(msg.to_json())
            logger.debug(f"Added message to transcript.")
    
    @traced
    def add_msg(self, msg: Message, db: Client, create_in_subcollection: bool=True) -> str:
        """ Add a message to the transcript. Also adds it to the appropriate subcollection.
        Returns:
            The message ID.
        """
        logger.debug(f"Adding message to transcript: {msg}")
        if self.status == 'final':
            raise ValueError(f"Cannot add message to final transcript: {self.docpath}")
        assert self.status == 'live', f"Invalid status for transcript: {self.status}"
        if self.messages is None:
            self.messages = []
        msg_id = msg.role.value.upper() + str(len(self.messages))
        self.messages.append(msg)
        self.update(db)
        if create_in_subcollection:
            self._send_msg_to_subcollection(msg, msg_id, db)
        else:
            logger.warning(f"Not creating message in subcollection, only in transcript doc body. No Functions will be triggered. Message: {msg}")
        return msg_id

    @traced
    def update_msg(self, msg: Message, mid: str, db: Client) -> None:
        """ Update a message in the transcript doc body, not in the subcollections.
        Args:
            msg: The message to update.
            mid: The message ID in the Transcript.
        """
        with logger.contextualize(msg_id=mid):
            logger.debug(f"Updating message in transcript: {msg}")
            doc = self.docref(db)
            doc.update({
                'messages': {
                    mid: msg.model_dump_json(exclude_none=True),
                }
            })
            logger.debug("Updated message in transcript.")

    def _read_subcollections(self, db: Client) -> None:
        """ Read the subcollections from Firestore. You can use this only when the status is live. """
        logger.warning("Using _read_subcollections results in up to 50x the number of reads per transcript load event.")
        umsgs = self.docref(db).collection('umsgs').stream()
        amsgs = self.docref(db).collection('amsgs').stream()
        for msg in chain(umsgs, amsgs):
            logger.debug(f"Got message from Fb: {msg.to_dict()}")
            self.messages.append(Message(**msg.to_dict()))
        self.messages = sorted(self.messages, key=lambda msg: msg.created_at)

    def _read_messages(self, db: Client) -> None:
        """ Read the messages from Firestore. Use this when the transcript is final. """
        doc = self.docref(db).get()
        if not doc.exists:
            raise ValueError(f"selfript document {self.docpath} does not exist in Firebase.")
        dat = doc.to_dict()
        logger.debug(f"Got transcript {doc.id} from Fb: {dat}")
        try:
            raw_msgs: dict[str, dict[str, str]] = dat['messages']
        except KeyError:
            logger.debug(f"Transcript {self.docpath} has no messages.")
            msgs = []
        else:
            msgs = [Message(**msg) for msg in raw_msgs.values()]
        self.messages = sorted(msgs, key=lambda msg: msg.created_at)

    @classmethod
    def read(cls, docpath: DocPath, db: Client) -> "Transcript":
        """ Read the document from Firestore. """
        tdoc = docpath.to_docref(db).get()
        if not tdoc.exists:
            raise ValueError(f"Document {docpath} does not exist in Firebase.")
        kwargs = cls._kwargs_from_docpath(docpath)
        kwargs.update(tdoc.to_dict())
        transc = Transcript(**kwargs)
        transc._read_messages(db)
        return transc

    def create(self, db: Client, **kwargs) -> None:
        """ Create the document in Firestore if it doesn't exist.
        Does NOT create the messages in the subcollections.
        Raises:
            AttributeError: If docpath is not set.
            AlreadyExists: If the document already exists.
        """
        payload = self.to_json()
        self.docref(db).create(payload, **kwargs)
        logger.debug(f"Created transcript: {self.docpath}")

    def delete(self, db: Client, **kwargs) -> None:
        """ Delete the document in Firestore. """
        for colnm in ('amsgs', 'umsgs'):
            col: CollectionReference = self.docref(db).collection(colnm)
            for msgdoc in col.stream():
                logger.debug(f"Deleting message from transcript: {msgdoc.id}")
                msgdoc.reference.delete()
        return self.docref(db).delete(**kwargs)