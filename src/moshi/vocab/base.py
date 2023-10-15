""" This is the base data model for vocabulary terms.
"""
from functools import cached_property

from pydantic import Field, BaseModel

from moshi.language import Language

class Vocab(BaseModel):
    """ Represents a vocabulary term.
    Args:
        term (str): The term itself.
        bcp47 (str): The BCP-47 language code of the term.
    Properties:
        lang (moshi.language.Language): The language of the term.
    """
    bcp47: str = Field(help="BCP-47 language code.", default=None)
    term: str = Field(help="As used in the source utterance.")

    @cached_property
    def lang(self) -> Language:
        """ The language of the term. """
        return Language(self.bcp47)
