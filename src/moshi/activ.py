""" Text to text completion functionality. Session logic. Transcription and synthesis of audio in moshi_audio, not here.
For design terms, see: https://refactoring.guru/design-patterns/catalog
"""
import enum
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Generic, TypeVar, ParamSpec

from google.cloud.firestore import Client, DocumentReference
from loguru import logger
from pydantic import BaseModel, field_validator, Field, ValidationInfo, computed_field

from .language import Language
from .msg import Message
from .prompt import Prompt
from .storage import FB, DocPath
from .utils import random_string
from .voice import Voice


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

def default_pid(atp: ActT, n=8) -> str:
    tod = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return random_string(n) + '-' + atp.value + '-' + tod

def default_aid(atp: ActT) -> str:
    return default_pid(atp, n=4)

class Plan(FB, Generic[T], ABC):
    """ The Plan is a strategy for a session. """
    atp: ActT = Field(help="Activity type.")
    aid: str = Field(help="Activity ID.")
    uid: str = Field(help="User ID.")
    pid: str = Field(help="Plan ID.", default_factory=default_pid)
    bcp47: str = Field(help="Language for the session.")
    prompt: Prompt = Field(default=None, help="Extra prompt for the session.")
    template: dict[str, str] = Field(default=None, help="Template for the activity prompt.")
    state: dict = None
    vocab: list[str] = None
    voice: Voice

    @field_validator('voice', mode='before')
    def convert_string_to_voice(cls, v: str) -> Voice:
        logger.debug(f"Got: {v}")
        if isinstance(v, str):
            logger.debug(f"Converting string to voice: {v}")
            v = Voice(v)
        return v

    @classmethod
    def _kwargs_from_docpath(cls, docpath: DocPath) -> dict:
        if len(docpath.parts) != 4:
            raise ValueError(f"Invalid docpath for plan, must have 4 parts: {docpath}")
        if docpath.parts[0] != 'users':
            raise ValueError(f"Invalid docpath for plan, first part must be 'users': {docpath}")
        if docpath.parts[2] != 'plans':
            raise ValueError(f"Invalid docpath for plan, third part must be 'plans': {docpath}")
        return {
            'uid': docpath.parts[1],
            'pid': docpath.parts[3],
        }

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

class UnstrPl(Plan[ActT.UNSTRUCTURED]):
    """ Most basic functional session plan. """
    atp: ActT = ActT.UNSTRUCTURED

class Act(FB, Generic[T], ABC):
    """ Implement session logic. """
    aid: str
    atp: ActT
    bcp47: str
    prompt: Prompt
    source: str = "builtin"

    @computed_field
    @property
    def lang(self) -> Language:
        return Language(self.bcp47)

    @classmethod
    def get_docpath(cls, atp: ActT | str, bcp47: str, aid: str) -> DocPath:
        atp = ActT(atp)
        return DocPath(f'acts/{atp.value}/{bcp47}/{aid}')

    @property
    def docpath(self) -> DocPath:
        return Act.get_docpath(self.atp, self.bcp47, self.aid)

    @classmethod
    def _kwargs_from_docpath(cls, docpath: DocPath) -> dict:
        if len(docpath.parts) != 4:
            raise ValueError(f"Invalid docpath for activity, must have 4 parts: {docpath}")
        if docpath.parts[0] != 'acts':
            raise ValueError(f"Invalid docpath for activity, first part must be 'acts': {docpath}")
        try:
            ActT(docpath.parts[1])
        except ValueError:
            raise ValueError(f"Invalid docpath for activity, second part must be a valid activity type, got: {docpath.parts[1]} from {docpath}")
        try:
            Language(docpath.parts[2])
        except ValueError:
            raise ValueError(f"Invalid docpath for activity, third part must be a valid bcp47 language code, got: {docpath.parts[2]} from {docpath}")
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

    @abstractmethod
    def reply(self, msgs: list[Message], plan: Plan[T]) -> str:
        """ This is to be called when a user message arrives. """
        ...

class MinA(Act[ActT.MIN]):
    """ Most basic activity implementation. Has no session logic. """
    atp: ActT = ActT.MIN
    aid: str = '000000-mina'  # a singular min activity
    prompt: Prompt = Prompt(msgs=[Message.from_string("Hello, world!", 'ast')])
    source: str = "builtin"

    def reply(self, msgs: list[Message], plan: Plan[ActT.MIN]) -> str:
        """ This is to be called when a user message arrives. """
        return Message('ast', "Hello, world!")

class UnstrA(Act[ActT.UNSTRUCTURED]):
    """ Most basic "functional" activity. Uses completion to generate a reply. """
    atp: ActT = ActT.MIN
    aid: str = Field(help="Activity ID.", default_factory=lambda: default_aid(ActT.UNSTRUCTURED))
    source: str = "builtin"

    def reply(self, msgs: list[Message], plan: Plan[ActT.UNSTRUCTURED]) -> str:
        """ This is to be called when a user message arrives. """
        self.prompt.msgs.extend(plan.prompt.msgs + msgs)
        return self.prompt.complete(vocab=plan.vocab)


PLAN_OF_TYPE = {
    ActT.MIN: MinPl,
    ActT.UNSTRUCTURED: UnstrPl,
}

ACT_OF_TYPE = {
    ActT.MIN: MinA,
    ActT.UNSTRUCTURED: UnstrA,
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
        raise KeyError(f"Plan {pid} does not have an activity type ('atp') attribute.")
    except ValueError:
        raise ValueError(f"Plan {pid} has an invalid activity type ('atp') attribute.")
    try:
        P = PLAN_OF_TYPE[atp]
        logger.debug(f"Found plan type {P} for plan {pid}.")
    except KeyError:
        raise KeyError(f"Plan {pid} has an invalid activity type. Only {PLAN_OF_TYPE.keys()} are supported at the moment.")
    dat['uid'] = uid
    dat['pid'] = pid
    return P(**dat)  # NOTE could use P.read() but this would incur an extra db read, so why not use the dat already here.

def plan2act(plan: Plan, db: Client) -> Act:
    """ Using the data in a Plan doc, determine the type of the activity and load it. """
    try:
        A = ACT_OF_TYPE[plan.atp]
        logger.debug(f"Found activity type {A} for plan {plan.pid}.")
    except KeyError:
        raise KeyError(f"Plan {plan.pid} has an invalid activity type. Only {ACT_OF_TYPE.keys()} are supported at the moment. Got: {plan.atp}")
    return A.read(A.get_docpath(plan.atp, plan.bcp47, plan.aid), db)

# EOF
# FUTURE


'''
class UnstrP(Plan[ActT.UNSTRUCTURED]):
    """ Most basic session plan. """
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
'''