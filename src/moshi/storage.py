""" Firebase storage models. """
import json
from abc import ABC, abstractclassmethod, abstractmethod, abstractproperty
from datetime import datetime, timezone
from pathlib import Path

from google.cloud.firestore import Client, DocumentReference
from loguru import logger
from pydantic import BaseModel, Field, field_validator

from . import utils
from .__version__ import __version__


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

class FB(Versioned, ABC):
    docpath: Path = None
    
    def to_dict(self, *args, mode='python', **kwargs) -> dict:
        kwargs['exclude'] = kwargs.get('exclude', []) + ['docpath']
        return super().to_dict(*args, mode=mode, **kwargs)
    
    def to_json(self, *args, mode='json', **kwargs) -> dict:
        kwargs['exclude'] = kwargs.get('exclude', []) + ['docpath']
        return super().to_json(*args, mode=mode, **kwargs)
    
    def docref(self, db: Client) -> DocumentReference:
        """ Get the document reference. 
        Raises:
            AttributeError: If docpath is not set.
        """
        return db.document(self.docpath.as_posix())
    
    @field_validator('docpath', mode='before')
    def coerce_docpath_to_path(cls, v) -> Path | None:
        if not v:
            return None
        if isinstance(v, Path):
            v = v.with_suffix('')
        elif isinstance(v, str):
            v = Path(v)
        elif isinstance(v, DocumentReference):
            v = Path(v.id)
        else:
            raise TypeError(f"Invalid type for docpath: {type(v)}")
        if len(v.parts) % 2:
            logger.debug(f"Length of docpath is not even: {v}")
            raise ValueError(f"Invalid docpath: {v}")
        return v

    def _load(self, db: Client = None) -> dict:
        """ Get the data from Firestore. """
        if self.docpath and not self._docref:
            self._docref = db.document(self.docpath.as_posix())
        return self._docref.get()

    @classmethod
    def from_fb(cls, docpath: str | Path | DocumentReference, db: Client = None) -> "FromFB":
        res = cls(docpath=docpath)
        res._load(db)

    def to_fb(self, db: Client) -> None:
        """ db client is optional when initialized with a DocumentReference.
        Raises:
            AttributeError: If docpath is not set.
        """
        self.docref(db).set(self.to_json(mode='fb'))

    def delete_fb(self, db: Client) -> None:
        """ Delete the document in Firebase. """
