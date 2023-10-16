""" The maturity of a typical speaker required for expected mastery of a term. """
from enum import IntEnum

from loguru import logger

class Level(IntEnum):
    """ The maturity of a typical speaker required for expected mastery of a term. """
    ERROR = 0
    BABY = 1
    CHILD = 2
    ADULT = 3
    EXPERT = 4

    @classmethod
    def to_ranking(cls) -> str:
        """ BABY, TODDLER, ... as a string. Useful for templating prompts. """
        return ', '.join([l.name for l in cls])

    @classmethod
    def from_str(cls, level: str) -> 'Level':
        """ Get a Level from a string. """
        try:
            return cls[level.upper()]
        except KeyError as exc:
            raise ValueError(f"Invalid level: {level}") from exc