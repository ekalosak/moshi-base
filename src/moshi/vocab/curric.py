""" This data model for vocabulary holds the most information about a term.
Its term is the key to the doc stored at /curric/vocab/<bcp47>/<term> doc.
The <bcp47> collection holds all the terms for a given language aprox. 30,000 terms.
"""
from pydantic import Field

from moshi.storage import FB
from moshi.grade import Level, Grade
from .base import Vocab

class CurricV(Vocab):
    """ Represents a vocabulary term in the curriculum. Holds the most information about a term. This is the reference material for sessions. See /curric/vocab/<bcp47>/<grade> doc.   """
    defn: str = Field(help="Definition of the term in the source language.bcp47.", default=None)
    pos: str = Field(help="Part of speech.", default=None)
    root: str = Field(help="Root form of the term. ", examples=["'went' -> 'to go' or 'go'", "'splendidly' -> 'splendid'"], default=None)
    conju: str = Field(help="Conjugation of the term. Only provided for verbs.", examples=["For 'went' it would be 'past tense'."], default=None)
    detail: str = Field(help="Additional details about the term.", default=None)
    examples: list[str] = Field(help="Examples of the term in use.", default=None)
    synonyms: list[str] = Field(help="Synonyms of the term.", default=None)
    level: Level = Field(help="The level of the term in the curriculum. Should align with `grade`.", default=None)
    grade: Grade = Field(help="The grade of the term in the curriculum. Should align with `level`.", default=None)