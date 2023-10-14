""" This data model for vocabulary holds the minimum information required in a session.
Its term is the key to the field stored in the /users/<uid>/transcripts/<tid> doc at .msgs.<mid>.vocab.<term>;
BCP-47 is derived from the doc's .lang field.
"""
from pydantic import Field

from .base import Vocab

class MsgV(Vocab):
    """ Represents a vocabulary term in a user session. As an element of a transcript doc, it hasn't its own FB serialization. """
    term: str = Field(help="The term itself.")
    udefn: str = Field(help="Micro-definition; revealed on click in a user session.", default=None)
    pos: str = Field(help="Part of speech.", default=None)