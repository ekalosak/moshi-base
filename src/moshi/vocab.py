from functools import cached_property

from pydantic import Field, BaseModel

from moshi.language import Language

class Vocab(BaseModel):
    """ Represents a vocabulary term. Only bcp47 and term are required.  """
    bcp47: str = Field(help="BCP-47 language code.", default=None)
    defn: str = Field(help="Definition of the term in the source language. See self.bcp47.", default=None)
    pos: str = Field(help="Part of speech.", default=None)
    term: str = Field(help="As used in the source utterance.")
    trs: dict[str, 'Vocab'] = Field(help="Translation of the term. Keys are BCP-47 language codes.", default=None)
    root: str = Field(help="Root form of the term. Usually provided for verbs.", examples=["For 'went' it would be 'to go'."], default=None)
    conju: str = Field(help="Conjugation of the term. Usually provided for verbs.", examples=["For 'went' it would be 'past tense'."], default=None)
    detail: str = Field(help="Additional details about the term.", default=None)

    @cached_property
    def lang(self) -> Language:
        """ The language of the term. """
        return Language(self.bcp47)
