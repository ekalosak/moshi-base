""" This data model for vocabulary holds the user's usage of terms over time.
"""
import datetime as d

from pydantic import BaseModel, Field

from moshi.storage import FB
from .base import Vocab

class Usage(BaseModel):
    """ One usage of a term. """
    tid: str = Field(help="The transcript id. /users/<uid>/transcripts/<tid>. ")
    mid: str = Field(help="The message id. Key in .tdoc.msgs field.")
    used_correctly: bool = Field(help="Whether the user used the term correctly.")
    when: d.datetime = Field(help="When the user used the term.", default_factory=d.datetime.now)

class UsageV(Vocab, FB):
    """ Represents a vocabulary term in the usage tracking system. Stored as /users/<uid>/vocab-<bcp47>/<term> doc.
    """
    term: str = Field(help="The term used.")
    usgs: list[Usage] = Field(help="Times the user used the term.")
    first: d.datetime = Field(help="The first time the user used the term.", default_factory=d.datetime.now)
    last: d.datetime = Field(help="The last time the user used the term.", default_factory=d.datetime.now)

    @property
    def count(self) -> int:
       """ Number of times the user used the term. """
       return len(self.usgs)

    @property
    def correct(self) -> int:
       """ Number of times the user used the term correctly. """
       return len([u for u in self.usgs if u.used_correctly])

    @property
    def incorrect(self) -> int:
       """ Number of times the user used the term incorrectly. """
       return len([u for u in self.usgs if not u.used_correctly])
    
    @property
    def pct_correct(self) -> float:
       """ Percentage of times the user used the term correctly. """
       return self.correct / self.count
