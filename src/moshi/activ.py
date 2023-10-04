""" Text to text completion functionality. Session logic. Transcription and synthesis of audio in moshi_audio, not here.
For design terms, see: https://refactoring.guru/design-patterns/catalog
"""
import enum
from abc import ABC, abstractclassmethod, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar, Literal

from google.cloud.firestore import Client, DocumentReference
from pydantic import BaseModel, field_validator, Field, ValidationInfo

from .func import Function
from .language import Language
from .msg import Message
from .prompt import Prompt
from .storage import FB, DocPath


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
    aid: str = Field(help="Activity ID.")
    pid: str = Field(help="Plan ID.")
    uid: str = Field(help="User ID.")
    atp: ActT = Field(help="Activity type.")
    lang: Language = Field(help="Language for the session.")
    functions: list[Function] = []
    prompt: Prompt = Prompt()
    template: dict[str, str] = {}
    state: dict = {}
    vocab: list[str] = []
    
    @property
    def docpath(self) -> DocPath:
        return DocPath(f'users/{self.uid}/plans/{self.pid}')

class MinPl(Plan[ActT.MIN]):
    """ Most basic session plan. """
    atp: ActT = ActT.MIN
    aid: str = '000000-min'

class Act(FB, Generic[T], ABC):
    """ Implement session logic. """
    aid: str
    atp: ActT
    lang: Language
    prompt: Prompt

    @field_validator('lang', mode='before')
    def coerce_lang_bcp47_str(cls, v):
        if isinstance(v, str):
            v = Language(bcp47=v)
        elif not isinstance(v, Language):
            raise TypeError(f"Invalid type for lang: {type(v)}")
        return v

    @property
    def docpath(self) -> DocPath:
        return DocPath(f'acts/{self.atp.value}/{self.lang.bcp47}/{self.aid}')

    @abstractmethod
    def reply(self, usr_msg: Message, plan: Plan[T]) -> str:
        """ This is to be called when a user message arrives. """
        ...

class MinA(Act[ActT.MIN]):
    """ Most basic activity implementation. """
    atp: ActT = ActT.MIN
    aid: str = '000000-min'
    prompt: Prompt = Prompt(msgs=[Message.from_string("Hello, world!", 'sys')])

    def __init__(self, bcp47: str, **kwargs):
        lang = Language(bcp47)
        super().__init__(lang=lang, **kwargs)

    def reply(self, usr_msg: Message, plan: Plan[ActT.MIN]) -> str:
        """ This is to be called when a user message arrives. """
        return "Hello, world!"

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