""" Text to text completion functionality. Session logic. Transcription and synthesis of audio in moshi_audio, not here.
For design terms, see: https://refactoring.guru/design-patterns/catalog
"""
from abc import ABC
import enum
from typing import TypeVar, Generic

from .msg import Message
from .prompt import Prompt
from .func import Function, Fu


class ActType(enum.Enum):
    """ Type of activity. """
    MIN = 0  # no nothing, users shouldn't receive this
    INTRO = 1  # name, pronouns, interests, etc.
    GUIDED = 2  # curriculum and learning goals, e.g. match colors and nouns; levels; win conditions
    SCENARIO = 3  # get a coffee; state; win conitions
    UNSTRUCTURED = 4  # only vocab and prompt
    LESSON = 5  # in native language, teach theory
    STORY = 6  # multi-scenario with a plot, persistent characters
    DRILL = 7  # practice, e.g. flashcards, fill in the blank, multiple choice, etc.

T = TypeVar('T', bound=ActType)

class Plan(ABC, Generic[T]):
    """ The Plan is a strategy for a session.
    """
    template: dict[str, str] = None
    vocab: list[str] = None
    functions: list[Function] = None
    prompt: Prompt = None

class Act(ABC, Generic[T]):
    """ Implement session logic. """
    def __init__(self, prompt: Prompt, plan: Plan[T]):
        self._aid = None
        self.prompt = prompt
        self.plan = plan
        if self.plan.template:
            self.prompt.substitute(self.plan.template)

    @property
    def aid(self) -> str | None:
        return self._aid

    def reply(self, usr_msg: Message) -> str:
        """ Respond to user prompt. """
        raise NotImplementedError

class MinimalP(Plan[ActType.MIN]):
    """ Most basic session plan. """
    ...

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
    # require template contains

class GuidedA(Act[ActType.GUIDED]):
    """ Guided activity implementation. Curriculum and learning goals.
    Examples:
        - Moshi will use colors and nouns. Describe the color of the object.
    """
    templ = {'level': 'novice', 'combine': 'colors and nouns'}
    ...