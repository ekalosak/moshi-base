"""This module provides a datamodel of the user profile."""
from datetime import datetime

from google.cloud.firestore import Client
from pydantic import BaseModel, Field

from .storage import FB, DocPath

class Streak(BaseModel):
    count: int=0
    last: datetime=Field(help="Last time user completed a lesson.", default_factory=datetime.now)

class User(FB):
    """Models the user profile."""
    uid: str
    name: str
    language: str
    native_language: str
    streak: Streak=Field(default_factory=Streak)

    @property
    def bcp47(self) -> str:
        return self.language

    @classmethod
    def from_uid(cls, uid: str, db: Client) -> 'User':
        return super().read(DocPath(f'users/{uid}'), db)

    @property
    def docpath(self) -> DocPath:
        return DocPath(f'users/{self.uid}')