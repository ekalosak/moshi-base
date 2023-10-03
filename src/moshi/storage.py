""" Firebase storage models. """
from datetime import datetime, timezone
import json
from abc import ABC, abstractclassmethod, abstractmethod
from datetime import datetime

from google.cloud.firestore import Client
from loguru import logger
from pydantic import BaseModel, field_validator, Field

from .__version__ import __version__
from . import utils

class Versioned(BaseModel, ABC):
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    base_version: str = __version__

    @field_validator('base_version')
    def check_version(cls, v):
        if v != __version__:
            logger.warning(f"Version mismatch: got {v} != base {__version__}")
        return v

    def to_dict(self, *args, mode='python', **kwargs) -> dict:
        """ Alias for BaseModel's model_dump. """
        return self.model_dump(*args, mode=mode, **kwargs)

    def to_json(self, *args, mode='json', **kwargs) -> dict:
        """ Alias for BaseModel's json-mode model_dump. """
        return self.model_dump(*args, mode=mode, **kwargs)

    def to_jsons(self, *args, **kwargs) -> str:
        return json.dumps(self.to_json(*args, **kwargs), default=utils.jsonify)

class FromFB(Versioned, ABC):
    """Load from Firestore."""

    @abstractclassmethod
    def from_fb(cls, db: Client) -> "FromFB":
        ...


class ToFB(Versioned, ABC):
    """Save to Firestore."""

    @abstractmethod
    def to_fb(self, db: Client) -> None:
        ...


class FB(FromFB, ToFB, ABC):
    """Load from and save to Firestore."""

    ...