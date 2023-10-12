from pydantic import Field, BaseModel


class Vocab(BaseModel):
    """ Represents a vocabulary term. Only bcp47 and term are required.  """
    bcp47: str = Field(help="BCP-47 language code.")
    definition: str = Field(help="Definition of the term in the source language. See self.bcp47.", default=None, alias="defn")
    part_of_speech: str = Field(help="Part of speech.", default=None, alias="pos")
    term: str = Field(help="As used in the source utterance.")
    translations: dict[str, 'Vocab'] = Field(help="Translation of the term. Keys are BCP-47 language codes.", default=None, alias="trs")
    root: str = Field(help="Root form of the term. Usually provided for verbs.", examples=["For 'went' it would be 'to go'."], default=None)
    conjugation: str = Field(help="Conjugation of the term. Usually provided for verbs.", examples=["For 'went' it would be 'past tense'."], default=None, alias="conj")