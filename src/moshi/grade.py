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

class Rankable(Enum):
    @classmethod
    def to_ranking(cls) -> str:
        """ Return the ranking of this object as a string. """
        ranking = [r.name for r in cls]
        return ', '.join(ranking)

class YesNo(FromStr, Rankable):
    """ A degree of correctness or truth, from no to yes. """
    NO = 'NO', 0
    SLIGHT = 'SLIGHT', 1
    SOMEWHAT = 'SOMEWHAT', 2
    MOSTLY = 'MOSTLY', 3 
    YES = 'YES', 4

class Level(Rankable):
    """ The maturity of a typical speaker required for expected mastery of a term. """
    ERROR = 'ERROR', 0
    BABY = 'BABY', 1
    CHILD = 'CHILD', 2
    ADULT = 'ADULT', 3
    EXPERT = 'EXPERT', 4
