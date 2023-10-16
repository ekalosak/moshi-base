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

class Rankable(IntEnum):
    @classmethod
    def to_ranking(cls) -> str:
        """ Return the ranking of this object as a string. """
        ranking = [r.name for r in cls]
        return ', '.join(ranking)

    # def __le__(self, other):
    #     return self.value <= other.value
    
    # def __ge__(self, other):
    #     return self.value >= other.value
    
    # def __lt__(self, other):
    #     return self.value < other.value
    
    # def __gt__(self, other):
    #     return self.value > other.value

    # def __sub__(self, other):
    #     if not isinstance(other, Rankable):
    #         raise TypeError(f"Unsupported operand type(s) for -: '{type(self).__name__}' and '{type(other).__name__}'")
    #     return self.value - other.value

class YesNo(FromStr, Rankable):
    """ A degree of correctness or truth, from no to yes. """
    NO = 0
    SLIGHT = 1
    SOMEWHAT = 2
    MOSTLY = 3 
    YES = 4

class Level(FromStr, Rankable):
    """ The maturity of a typical speaker required for expected mastery of a term.
    NOTE See the prompts (e.g. msg_score_vocab.txt) for the exact definitions of each level.
    NOTE Don't change the string representations of these values without updating the prompts.
    """
    ERROR = 0
    BABY = 1
    CHILD = 2
    ADULT = 3
    EXPERT = 4

