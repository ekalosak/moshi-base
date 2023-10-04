""" Text to text completion functionality. Session logic. Transcription and synthesis of audio in moshi_audio, not here.
For design terms, see: https://refactoring.guru/design-patterns/catalog
"""
import enum
from abc import ABC, abstractclassmethod, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Generic, TypeVar, Literal

from google.cloud.firestore import Client, DocumentReference
from pydantic import BaseModel, field_validator, Field, ValidationInfo

from .func import Function
from .language import Language
from .msg import Message
from .prompt import Prompt
from .storage import FB, DocPath
from .utils import random_string


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

def default_pid(atp: ActT) -> str:
    tod = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return random_string(12) + '-' + atp.value + '-' + tod

class Plan(FB, Generic[T], ABC):
    """ The Plan is a strategy for a session. """
    atp: ActT = Field(help="Activity type.")
    aid: str = Field(help="Activity ID.")
    uid: str = Field(help="User ID.")
    pid: str = Field(help="Plan ID.", default_factory=default_pid)
    bcp47: str = Field(help="Language for the session.")
    prompt: Prompt = Field(default=None, help="Extra prompt for the session.")
    template: dict[str, str] = None
    state: State = None
    vocab: list[str] = None

    @classmethod
    def from_act(cls, act: 'Act[T]', uid: str, **kwargs) -> 'Plan[T]':
        """ Create a plan from an activity. """
        return cls(
            atp=act.atp,
            aid=act.aid,
            uid=uid,
            bcp47=act.bcp47,
            **kwargs 
        )

    @property
    def docpath(self) -> DocPath:
        if not self.uid:
            raise ValueError("Cannot get docpath for plan without uid.")
        elif not self.pid:
            raise ValueError("Cannot get docpath for plan without pid.")
        return DocPath(f'users/{self.uid}/plans/{self.pid}')

    def to_json(self, *args, exclude=['pid', 'uid'], exclude_unset=True, **kwargs) -> dict:
        """ Get the data to write to Firestore.
        Args:
            exclude: Fields to exclude from the returned dict. Defaults to those attributes in the docpath (pid, uid).
        """
        return super().to_json(*args, exclude=exclude, exclude_unset=exclude_unset, **kwargs)

class MinPl(Plan[ActT.MIN]):
    """ Most basic session plan. """
    atp: ActT = ActT.MIN
    aid: str = '000000-mina'  # a singular min activity
    pid: str = '000000-minp'  # a singular min plan for each user subscribed

class Act(FB, Generic[T], ABC):
    """ Implement session logic. """
    _lang: Language
    aid: str
    atp: ActT
    bcp47: str
    prompt: Prompt
    source: str = "builtin"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lang = Language(self.bcp47)

    @property
    def docpath(self) -> DocPath:
        return DocPath(f'acts/{self.atp.value}/{self.bcp47}/{self.aid}')

    @classmethod
    def _kwargs_from_docpath(cls, docpath: DocPath) -> dict:
        if docpath.parts[0] != 'acts':
            raise ValueError(f"Invalid docpath for activity, first part must be 'acts': {docpath}")
        if len(docpath.parts) != 4:
            raise ValueError(f"Invalid docpath for activity, must have 4 parts: {docpath}")
        return {
            'atp': ActT(docpath.parts[1]),
            'bcp47': docpath.parts[2],
            'aid': docpath.parts[3],
        }

    def to_json(self, *args, exclude=['aid', 'atp'], exclude_none=True, **kwargs) -> dict:
        """ Get the data to write to Firestore.
        Args:
            exclude: Fields to exclude from the returned dict. Defaults to those attributes in the docpath (aid).
        """
        return super().to_json(*args, exclude=exclude, exclude_none=exclude_none, **kwargs)

    @property
    def lang(self) -> Language:
        return self._lang

    @abstractmethod
    def reply(self, usr_msg: Message, plan: Plan[T]) -> str:
        """ This is to be called when a user message arrives. """
        ...

class MinA(Act[ActT.MIN]):
    """ Most basic activity implementation. """
    atp: ActT = ActT.MIN
    aid: str = '000000-mina'  # a singular min activity
    prompt: Prompt = Prompt(msgs=[Message.from_string("Hello, world!", 'ast')])
    source: str = "builtin"

    def __init__(self, bcp47: str=None, **kwargs):
        super().__init__(bcp47=bcp47, **kwargs)

    def reply(self, usr_msg: Message, plan: Plan[ActT.MIN]) -> str:
        """ This is to be called when a user message arrives. """
        return "Hello, world!"

ACTIVITIES = {
    ActT.MIN: MinA,
}

def pid2plan(pid: str, uid: str, db: Client) -> Plan:
    """ From the data in a Plan doc, determine the type of the plan and load it. """
    ds = DocPath(f'users/{uid}/plans/{pid}').to_docref(db).get()
    if not ds.exists:
        raise KeyError(f"Plan {pid} does not exist.")
    dat = ds.to_dict()
    try:
        atp = ActT(dat['atp'])
    except KeyError:
        raise KeyError(f"Plan {pid} does not have an activity type.")
    except ValueError:
        raise ValueError(f"Plan {pid} has an invalid activity type.")
    try:
        act = ACTIVITIES[atp]
    except KeyError:
        raise KeyError(f"Plan {pid} has an invalid activity type. Only {ACTIVITIES.keys()} are supported at the moment.")
    return act(**dat)

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

PLAN_OF_TYPE = {
    ActT.MIN: MinPl
}

ACT_OF_TYPE = {
    ActT.MIN: MinA
}