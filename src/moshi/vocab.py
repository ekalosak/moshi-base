from pydantic import Field
from .storage import FB


# FB inherits pydantic.BaseModel
class Vocab(FB):
    """ Represents a vocabulary term.
    """
    bcp47: str = Field(help="BCP-47 language code.")
    defn: str = Field(help="Definition of the term in the source language. See self.bcp47.", default=None, alias="definition")
    pos: str = Field(help="Part of speech.", default=None, alias="part_of_speech")
    term: str = Field(help="As used in the source utterance.")
    translations: dict[str, 'Vocab'] = Field(help="Translation of the term. Keys are BCP-47 language codes.", default=None, alias="trs")
    root: str = Field(help="Root form of the term. Usually provided for verbs.", examples=["For 'went' it would be 'to go'."], default=None)
    conj: str = Field(help="Conjugation of the term. Usually provided for verbs.", examples=["For 'went' it would be 'past tense'."], default=None, alias="conjugation")