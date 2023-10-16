""" The maturity of a typical speaker required for expected mastery of a term. """
from abc import ABC, abstractmethod
from typing import TypeVar
from enum import EnumType, IntEnum

from loguru import logger
from enum import Enum

class FromStr(Enum):
    @classmethod
    def from_str(cls, str_repr: str) -> 'FromStr':
        """ Get an instance of this class from a string representation. """
        try:
            return cls[str_repr.upper()]
        except KeyError as exc:
            raise ValueError(f"Invalid string representation for {cls.__name__}: {str_repr}") from exc

class Rankable(IntEnum, FromStr):
    @classmethod
    def to_ranking(cls) -> str:
        """ Return the ranking of this object as a string. """
        ranking = [r.name for r in cls]
        return ', '.join(ranking)

class YesNo(Rankable):
    """ A degree of correctness or truth, from no to yes. """
    NO = 0
    SLIGHT = 1
    SOMEWHAT = 2
    MOSTLY = 3 
    YES = 4

class Level(Rankable):
    """ The maturity of a typical speaker required for expected mastery of a term.
    NOTE See the prompts (e.g. msg_score_vocab.txt) for the exact definitions of each level.
    NOTE Don't change the string representations of these values without updating the prompts.
    """
    ERROR = 0
    BABY = 1
    CHILD = 2
    ADULT = 3
    EXPERT = 4

