"""This module provides a datamodel of the user profile."""
from .storage import FB, DocPath

class User(FB):
    """Models the user profile."""
    uid: str
    name: str
    language: str
    native_language: str

    @property
    def docpath(self) -> DocPath:
        return DocPath(f'users/{self.uid}')