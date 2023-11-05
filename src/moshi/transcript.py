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
from datetime import datetime
from itertools import chain
from typing import TypeVar

from google.cloud.firestore import Client, CollectionReference
from google.cloud.exceptions import Conflict
from google.cloud.firestore import DocumentReference, DocumentSnapshot
from loguru import logger
from pydantic import BaseModel, Field, field_validator, ValidationInfo, computed_field

from . import utils
from .activ import ActT, Plan
from .grade import Grade
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
    n: int

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
    messages: dict[str, Message] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utils.utcnow, help='Time of creation.')
    aid: str = Field(help='Activity ID.')
    atp: ActT = Field(help='Activity type.')
    pid: str = Field(help='Plan ID.')
    uid: str = Field(help='User ID.')
    bcp47: str = Field(help='User language e.g. "en-US".')
    tid: str = Field(None, help='Transcript ID. One is created if not provided.', validate_default=True)
    summary: str = None
    grade: Grade=Field(None, help='Overall grade. Created upon finalization.')
    topics: list[str]=Field(None, help='Topic tags. Created upon finalization.')
    assessment: str=Field(None, help='A brief assessment of user language skill. Created upon finalization.')
    status: str = Field('live', help='Transcript status. One of "live", "final", or "empty".')
    feedback: str = Field(None, help='User feedback. One of "good", "bad", "none", or "abandoned". Created upon finalization.')

    @property
    def msgs(self) -> list[Message]:
        """ Get the list of messages, sorted by date, from this transcript. """
        if not self.messages:
            return []
        return sorted(self.messages.values(), key=lambda msg: msg.created_at)

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
        _all: dict[str, list[int]] = {}
        for msg in self.messages.values():  # no need to sort, we're just aggregating
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
            medians[name] = median(vals)
            mads[name] = median([abs(val - medians[name]) for val in vals])
        scost_pld = {}
        for name in ('vocab', 'grammar', 'idiom', 'polite', 'context'):
            if name in medians:
                scost_pld[name] = ScoreT(median=medians[name], mad=mads[name], n=len(_all[name]))
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

    @property
    def last_updated(self) -> datetime:
        """ Get the last updated time from the messages, if there are messages. Otherwise get the created_at time. """
        if not self.messages:
            logger.debug(f"No messages in transcript, returning created_at: {self.created_at}")
            return self.created_at
        dt = None
        _msg = None
        for msg in self.msgs:
            if not dt or msg.created_at > dt:
                dt = msg.created_at
                _msg = msg
        logger.debug(f"Got last_updated from messages: {_msg}: {dt}")
        return dt

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
    def from_ref(cls, ref: 'DocumentReference', db) -> 'Transcript':
        """ Get a transcript from a document reference. """
        return cls.from_ids(ref.parent.parent.id, ref.id, db)

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
                for i, msg in enumerate(self.msgs)
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
    def add_msg(self, msg: Message, db: Client=None, create_in_subcollection: bool=True) -> str:
        """ Add a message to the transcript. Also adds it to the appropriate subcollection.
        Args:
            msg: The message to add.
            db: The Firestore client. If None, msg added only to self.messages.
            create_in_subcollection: Whether to create the message in the subcollection. If False, only creates the message in the transcript doc body so no Functions will be triggered. Default True. Ignored if db is None.
        Returns:
            The message ID.
        """
        logger.debug(f"Adding message to transcript: {msg.to_dict()}")
        if self.status != 'live':
            raise ValueError(f"Cannot add message to transcript with status={self.status}: {self.docpath}")
        msg_id = msg.role.value.upper() + str(len(self.messages))
        self.messages[msg_id] = msg
        if db:
            self.update(db)
            if create_in_subcollection:
                self._send_msg_to_subcollection(msg, msg_id, db)
            else:
                with logger.contextualize(**msg.to_dict()):
                    logger.warning(f"Not creating message in subcollection, only in transcript doc body. No Functions will be triggered.")
        return msg_id

    def add_msgs(self, msgs, db=None, cisubcol=True):
        """ Add multiple messages to the transcript. See `add_msg` for details. """
        for msg in msgs:
            self.add_msg(msg, db, cisubcol)

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
                    mid: msg.model_dump(exclude_none=True),
                }
            })
            logger.debug("Updated message in transcript.")

    def _read_subcollections(self, db: Client) -> None:
        """ Read the subcollections from Firestore. You can use this only when the status is live. """
        logger.warning("Using _read_subcollections results in up to 50x the number of reads per transcript load event.")
        umsgs = self.docref(db).collection('umsgs').stream()
        amsgs = self.docref(db).collection('amsgs').stream()
        for msgd in chain(umsgs, amsgs):
            msgd: DocumentSnapshot
            dat = msgd.to_dict()
            logger.debug(f"Got message from Fb: {msgd.id}: {dat}")
            self.messages[msgd.id] = Message(**dat)

    def _read_messages(self, doc: DocumentSnapshot) -> None:
        """ Read the messages from Firestore into self.messages. """
        if not doc.exists:
            raise ValueError(f"Transcript document {self.docpath} does not exist in Firebase.")
        dat = doc.to_dict()
        logger.debug(f"Got transcript {doc.id} from Fb: {dat}")
        try:
            raw_msgs: dict[str, dict[str, str]] = dat['messages']
        except KeyError:
            logger.debug(f"Transcript {self.docpath} has no messages.")
        else:
            for mid, _msg in raw_msgs.items():
                if 'mid' in _msg:
                    _mid = _msg.pop('mid')
                    logger.warning(f"Message {mid} has an unexpected `mid` attribute in its FB data: '{_mid}'. The former will be used.")
                msg = Message(**_msg)
                self.messages[mid] = msg

    @classmethod
    def read(cls, docpath: DocPath, db: Client) -> "Transcript":
        """ Read the document from Firestore. """
        tdoc = docpath.to_docref(db).get()
        if not tdoc.exists:
            raise ValueError(f"Document {docpath} does not exist in Firebase.")
        kwargs = cls._kwargs_from_docpath(docpath)
        kwargs.update(tdoc.to_dict())
        if 'messages' in kwargs:
            kwargs.pop('messages')
        transc = Transcript(**kwargs)
        transc._read_messages(tdoc)
        return transc

    def refresh(self, db: Client):
        super().refresh(db, uid=self.uid, tid=self.tid)

    def delete(self, db: Client, **kwargs) -> None:
        """ Delete the document in Firestore. """
        for colnm in ('amsgs', 'umsgs'):
            col: CollectionReference = self.docref(db).collection(colnm)
            for msgdoc in col.stream():
                logger.debug(f"Deleting message from transcript: {msgdoc.id}")
                msgdoc.reference.delete()
        return self.docref(db).delete(**kwargs)

    def finalize(self, db) -> str:
        """ Idempotently finalize the transcript.
        First, change the status to 'final' if there are messages, otherwise 'empty'.
        Next, add a sentinel doc to self.docpath/status/<status>. This triggers the appropriate finalization functions, including:
            - user streak update
            - grade transcript
            - etc.
        Returns:
            str: The transcript status.
        """
        self.status = 'empty'
        if self.messages:
            if any(msg.role == 'usr' for msg in self.msgs):
                self.status = 'final'
        self.update(db)
        logger.debug(f"Updated transcript status to: {self.status}")
        _dp = self.docpath
        dp = DocPath(_dp._path / f'status/{self.status}')
        try:
            dp.to_docref(db).create({})
        except Conflict:
            logger.debug(f"Status {dp} already exists.")
        logger.info(f"Finalized transcript: status={self.status} feedback={self.feedback}")
        return self.status