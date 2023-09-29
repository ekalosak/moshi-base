"""This module provides a datamodel of the user profile."""
from firebase_functions.firestore_fn import DocumentSnapshot
from google.cloud.firestore_v1 import Client
from loguru import logger

from .exceptions import ParseError
from .versioned import Versioned

class User(Versioned):
    """Models the user profile."""
    uid: str
    name: str
    language: str
    native_language: str

    @classmethod
    def get(cls, uid: str, db: Client) -> "User":
        """Get the Firestore document reference for this user."""
        doc: DocumentSnapshot = db.collection("users").document(uid).get()
        if not doc.exists:
            raise ValueError(f"User does not exist: {uid}")
        try:
            usr = User(uid=uid, **doc.to_dict())
        except Exception as e:
            logger.error(e)
            raise ParseError(f"Error parsing user: {uid}")
        return usr

    def create(self, db: Client):
        """Write the user to Firestore."""
        doc = db.collection("users").document(self.uid)
        if doc.get().exists:
            raise ValueError(f"User already exists: {self.uid}")
        doc.create(self.to_dict(exclude=["uid"]))