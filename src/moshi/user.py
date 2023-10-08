"""This module provides a datamodel of the user profile."""
from google.cloud.firestore import Client

from .storage import FB, DocPath

class User(FB):
    """Models the user profile."""
    uid: str
    name: str
    language: str
    native_language: str

    @property
    def bcp47(self) -> str:
        return self.language

    @classmethod
    def from_uid(cls, uid: str, db: Client) -> 'User':
        return super().read(DocPath(f'users/{uid}'), db)

    @property
    def docpath(self) -> DocPath:
        return DocPath(f'users/{self.uid}')