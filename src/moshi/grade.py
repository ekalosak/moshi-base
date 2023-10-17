""" The maturity of a typical speaker required for expected mastery of a term. """
from enum import Enum, IntEnum
from math import exp
from typing import Generator

from pydantic import BaseModel

from . import utils

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


class Grade(Rankable):
    """ Granular levels of education. """
    BABY = 0
    TODDLER = 1
    PRESCHOOL = 2
    KINDERGARTEN = 3
    FIRSTGRADE = 4
    SECONDGRADE = 5
    THIRDGRADE = 6
    FOURTHGRADE = 7
    FIFTHGRADE = 8
    MIDDLESCHOOL = 9
    HIGHSCHOOL = 10
    ADULT = 11
    COLLEGE = 12
    SPECIALIST = 13
    EXPERT = 14


class Score(BaseModel):
    """ How good is an element of a user session? """
    score: Grade | Level | YesNo
    explain: str = None

    def __init__(self, score: Level, explain: str=None):
        if not explain:
            super().__init__(score=score)
        else:
            super().__init__(score=score, explain=explain)

class Scores(BaseModel):
    """ Standard set of scores for a message. """
    vocab: Score = None
    grammar: Score = None
    idiom: Score = None
    polite: Score = None
    context: Score = None

    @property
    def each(self) -> Generator[tuple[str, Score], None, None]:
        """ Iterate over each score. """
        for name, score in self.__dict__.items():
            if score is not None:
                yield (name, score)

    def to_json(self, exclude_none=True, **kwargs):
        """ Convenience method to convert to consise JSON. """
        return self.model_dump(exclude_none=exclude_none, **kwargs)

    def to_fb(self, mid: str) -> dict:
        """ Convert to a dictionary for Firebase.
        That is, for nested dictionary representation, collapse into a flat dictionary.
        The keys are then the field paths in the transcript document, concattenated with '.'.
        For example: {'foo': {'fizz': 'bar'}} -> {'foo.fizz': 'bar'}
        """
        return utils.flatten({'messages': {mid: {'score': self.to_json()}}})
        