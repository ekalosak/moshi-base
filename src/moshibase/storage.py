""" Firebase storage models. """
import datetime
import json
from abc import ABC, abstractclassmethod, abstractmethod
from datetime import datetime

from google.cloud.firestore import Client
from pydantic import BaseModel, validator

from .__version__ import __version__
# from .utils import jsonify


class Versioned(BaseModel, ABC):
    created_at: datetime
    base_version: str = __version__

    @validator("created_at", pre=True, always=True)
    def set_created_at(cls, v):
        return v or datetime.now()

    def to_jsons(self, exclude: list[str] = None) -> str:
        """Dump the model as a JSON string."""
        return self.model_dump_json(exclude=exclude) #json.dumps(..., default=lambda o: jsonify(o))

    def to_json(self, exclude: list[str] = None) -> dict:
        """Dump the model as a JSON object."""
        return json.loads(self.to_jsons(exclude=exclude))


class FromFB(ABC):
    """Load from Firestore."""

    @abstractclassmethod
    def from_fb(cls, db: Client) -> "FromFB":
        ...


class ToFB(ABC):
    """Save to Firestore."""

    @abstractmethod
    def to_fb(self, db: Client) -> None:
        ...


class FB(FromFB, ToFB):
    """Load from and save to Firestore."""

    ...
