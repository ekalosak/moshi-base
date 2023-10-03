""" Text to text completion functionality. Session logic. Transcription and synthesis of audio in moshi_audio, not here.
For design terms, see: https://refactoring.guru/design-patterns/catalog
"""
from abc import ABC, abstractmethod, abstractclassmethod
import enum
from typing import TypeVar, Generic

from google.cloud.firestore import Client
from pydantic import BaseModel, validator

from .msg import Message
from .prompt import Prompt
from .func import Function
from .storage import FB


class ActType(enum.Enum):
    """ Type of activity. """
    MIN = 0  # no nothing, users shouldn't receive this
    INTRO = 1  # name, pronouns, interests, why learning this lang, learning goals.
    GUIDED = 2  # curriculum and learning goals, e.g. match colors and nouns; levels; win conditions
    SCENARIO = 3  # get a coffee; state; win conitions
    UNSTRUCTURED = 4  # only vocab and prompt
    LESSON = 5  # in native language, teach theory
    STORY = 6  # multi-scenario with a plot, persistent characters
    DRILL = 7  # practice, e.g. flashcards, fill in the blank, multiple choice, etc.
    ASSESSMENT = 8  # assess skills

T = TypeVar('T', bound=ActType)

class State(BaseModel):
    user: dict = None  # user name, pronouns, interests, etc.
    characters: list[str] = None  #

class Plan(BaseModel, Generic[T], FB, ABC):
    """ The Plan is a strategy for a session. """
    _pid: str = None
    _aid: str = None
    functions: list[Function] = None
    prompt: Prompt = None
    template: dict[str, str] = None
    state: dict = None
    vocab: list[str] = None

    @property
    def pid(self) -> str | None:
        return self._pid
    
    @property
    def aid(self) -> str | None:
        return self._aid
    

class Act(BaseModel, Generic[T], FB, ABC):
    """ Implement session logic. """
    _aid: str = None
    prompt: Prompt
    plan: Plan[T]

    @property
    def aid(self) -> str | None:
        return self._aid

    def reply(self, usr_msg: Message) -> str:
        """ Respond to user prompt. """
        raise NotImplementedError

class MinP(Plan[ActType.MIN]):
    """ Most basic session plan. """
    ...        

class MinA(Act[ActType.MIN]):
    """ Most basic activity implementation. """
    ...

# EOF
# FUTURE

class UnstrP(Plan[ActType.UNSTRUCTURED]):
    """ Most basic session plan. """
    ...


class UnstrA(Act[ActType.UNSTRUCTURED]):
    """ Most basic activity implementation.
    All it needs to do is respond to the user using the prompt.
    No functions. No templated plan. No level. Only vocab and prompt.
    """
    ...

class ScenarU(Act[ActType.SCENARIO]):
    """ Scenario activity implementation. """
    # require template contains state and win conditions
    ...


class GuidedA(Act[ActType.GUIDED]):
    """ Guided activity implementation. Curriculum and learning goals.
    Examples:
        - Moshi will use colors and nouns. Describe the color of the object.
    """
    templ = {'level': 'novice', 'combine': 'colors and nouns'}
    ...