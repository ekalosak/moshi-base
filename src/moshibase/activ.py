""" Text to text completion functionality. Session logic. Transcription and synthesis of audio in moshi_audio, not here. """
from abc import ABC
import enum
from typing import TypeVar, Generic

from .msg import Message
from .prompt import Prompt

class ActType(enum.Enum):
    """ Type of activity. """
    UNSTRUCTURED = 1
    GUIDED = 2
    INTRO = 3
    SCENARIO = 4
    LESSON = 5
    STORY = 6
    DRILL = 7

T = TypeVar('T', bound=ActType)

class Plan(ABC, Generic[T]):
    """ Strategy for Activity. Includes vocab, grammar, topics, specific instructions e.g. 'colors and nouns' """
    ...

class Act(ABC, Generic[T]):
    """ Implement session logic.
        - All Activities inject language skill aspects (vocab, grammar, etc.) into the session.
    """
    def __init__(self, prompt: Prompt, plan: Plan[T]):
        self._aid = None
        self.prompt = prompt
        self.plan = plan

    @property
    def aid(self) -> str | None:
        return self._aid

    def reply(self, usr_msg: Message) -> str:
        """ Respond to user prompt. """
        raise NotImplementedError

class Unstructured(Act[ActType.UNSTRUCTURED]):
    """ Most basic activity implementation. Simply responds to user using prompt. """
    ...

class Guided(Act[ActType.GUIDED]):
    """ Guided activity implementation. Curriculum and learning goals.
    Examples:
        - Moshi will use colors and nouns. Describe the color of the object.
    """
    raise NotImplementedError