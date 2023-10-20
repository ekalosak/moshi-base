""" This data model for vocabulary holds the user's usage of terms over time.
"""
from datetime import datetime

from pydantic import BaseModel, Field

from moshi.storage import FB
from moshi import utils
from .base import Vocab

class Usage(BaseModel):
    """ One usage of a term. """
    tid: str = Field(help="The transcript id. /users/<uid>/transcripts/<tid>. ")
    mid: str = Field(help="The message id. Key in .tdoc.msgs field.")
    used_correctly: bool = Field(help="Whether the user used the term correctly.")
    when: datetime = Field(help="When the user used the term.", default_factory=utils.utcnow)

class UsageV(Vocab, FB):
   """ Represents a vocabulary term in the usage tracking system. Stored as /users/<uid>/vocab-<bcp47>/<term> doc.
   """
   usgs: list[Usage] = Field(help="Times the user used the term.")
   first: datetime = Field(help="The first time the user used the term.", default_factory=utils.utcnow)
   last: datetime = Field(help="The last time the user used the term.", default_factory=utils.utcnow)

   @property
   def count(self, tid: str=None) -> int:
      """ Number of times the user used the term.
      If tid is given, count only the times the user used the term in that transcript.
      """
      if tid:
         return len([u for u in self.usgs if u.tid == tid])
      else:
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
