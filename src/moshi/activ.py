""" Text to text completion functionality. Session logic. Transcription and synthesis of audio in moshi_audio, not here.
For design terms, see: https://refactoring.guru/design-patterns/catalog
"""
import enum
from abc import ABC, abstractclassmethod, abstractmethod
from typing import Generic, TypeVar

from google.cloud.firestore import Client, DocumentReference
from pydantic import BaseModel, field_validator, Field

from .func import Function
from .language import Language
from .msg import Message
from .prompt import Prompt
from .storage import FB


class ActT(str, enum.Enum):
    """ Type of activity. Members ordered by level. """
    MIN = 'min'  # no nothing, users shouldn't receive this
    INTRO = 'intro'  # name, pronouns, interests, why learning this lang, learning goals.
    GUIDED = 'guided'  # curriculum and learning goals, e.g. match colors and nouns; levels; win conditions
    SCENARIO = 'scen'  # get a coffee; state; win conitions
    UNSTRUCTURED = 'unstr'  # only vocab and prompt
    LESSON = 'lesson'  # in native language, teach theory
    STORY = 'story'  # multi-scenario with a plot, persistent characters
    DRILL = 'drill'  # practice, e.g. flashcards, fill in the blank, multiple choice, etc.
    ASSESSMENT = 'asmt'  # assess skills

T = TypeVar('T', bound=ActT)

class State(BaseModel):
    user: dict = None  # user name, pronouns, interests, etc.
    characters: list[str] = None  #

class Plan(FB, Generic[T], ABC):
    """ The Plan is a strategy for a session. """
    # _atp: ActT = Field(help="Activity type.")
    # _lang: Language = Field(help="Language of the session.")
    aid: str
    functions: list[Function] = []
    prompt: Prompt = Prompt()
    template: dict[str, str] = {}
    state: dict = {}
    vocab: list[str] = []
    pid: str = None
    uid: str = None

    def docref(self, db: Client) -> DocumentReference:
        """ Where to put in Fb. """
        if not all((self.aid, self.pid, self.uid)):
            raise ValueError("Must set all aid, pid, uid before saving to FB.")
        return db.collection('users').document(self.uid).collection('plans').document(self.pid)

    def to_fb(self, db: Client):
        self.docref(db).set(self.to_json(mode='fb'))

class MinPl(Plan[ActT.MIN]):
    """ Most basic session plan. """
    _type: type = ActT.MIN
    aid: str = '000000-min'

class Act(FB, Generic[T], ABC):
    """ Implement session logic. """
    _atp: ActT
    _source: str = None  # whether 'hand' or 'some-fb-id'
    lang: Language | str
    prompt: Prompt
    plan: Plan[T]
    aid: str = None

    @field_validator('lang')
    def coerce_lang_bcp47_str(cls, v):
        if isinstance(v, str):
            return Language.from_bcp47(v)
        return v

    def docref(self, db: Client) -> DocumentReference:
        """ Where to put in Fb. """
        if not self.aid:
            raise ValueError("Must set aid before saving to FB.")
        return db.collection('acts').document(self.aid).collection('plans').document(self.pid)

    @classmethod
    def from_fb(cls, db: Client) -> 'Plan':
        ...

    def to_fb(self, db: Client):
        self.docref(db).set(self.to_json(mode='fb'))

    def reply(self, usr_msg: Message) -> str:
        """ This is to be called when a user message arrives. """
        raise NotImplementedError

class MinA(Act[ActT.MIN]):
    """ Most basic activity implementation. """
    _atp: ActT = ActT.MIN
    aid: str = '000000-min'
    prompt: Prompt = Prompt(msgs=[Message.from_string("Hello, world!", 'sys')])
    plan: MinPl = MinPl()

# EOF
# FUTURE

class UnstrP(Plan[ActT.UNSTRUCTURED]):
    """ Most basic session plan. """
    ...


class UnstrA(Act[ActT.UNSTRUCTURED]):
    """ Most basic activity implementation.
    All it needs to do is respond to the user using the prompt.
    No functions. No templated plan. No level. Only vocab and prompt.
    """
    ...

class ScenarU(Act[ActT.SCENARIO]):
    """ Scenario activity implementation. """
    # require template contains state and win conditions
    ...


class GuidedA(Act[ActT.GUIDED]):
    """ Guided activity implementation. Curriculum and learning goals.
    Examples:
        - Moshi will use colors and nouns. Describe the color of the object.
            - template = {'level': 'novice', 'combine': 'colors and nouns'}
    """
    ...