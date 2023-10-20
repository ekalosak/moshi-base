"""This module provides a datamodel of the user profile."""
from datetime import datetime

from google.cloud.firestore import Client
from pydantic import BaseModel, Field

from . import utils
from .storage import FB, DocPath

class Streak(BaseModel):
    count: int=0
    last: datetime=Field(None, help="Last time user completed a lesson.")
    tid: str=Field(None, help="Last transcript id.")

class User(FB):
    """Models the user profile."""
    uid: str
    name: str
    language: str
    native_language: str
    streak: Streak=Field(default_factory=Streak)
    created_at: datetime=Field(default_factory=utils.utcnow)

    @property
    def bcp47(self) -> str:
        return self.language

    @property
    def docpath(self) -> DocPath:
        return DocPath(f'users/{self.uid}')

    @classmethod
    def from_uid(cls, uid: str, db: Client) -> 'User':
        return super().read(DocPath(f'users/{uid}'), db)
