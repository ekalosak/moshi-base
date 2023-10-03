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
        """ Stringify the json with utils.jsonify. """
        return json.dumps(self.to_json(*args, **kwargs), default=utils.jsonify)

class DocPath(Path):
    """ A path to a document in Firestore. """

    def __init__(self, path: str | Path | DocumentReference):
        if isinstance(path, Path):
            path = path.with_suffix('')
        elif isinstance(path, str):
            path = Path(path)
        elif isinstance(path, DocumentReference):
            path = Path(path.id)
        else:
            raise TypeError(f"Invalid type for path: {type(path)}")
        if len(path.parts) % 2:
            logger.debug(f"Length of path is not even: {path}")
            raise ValueError(f"Invalid path: {path}")
        self._path = path

    def __str__(self):
        return self._path.as_posix()
    
    def to_docref(self, db: Client) -> DocumentReference:
        return db.document(self._path.as_posix())

class FB(Versioned, ABC):

    @abstractproperty
    def docpath(self) -> DocPath:
        """ The path to the document in Firestore. """
        ...

    def docref(self, db: Client) -> DocumentReference:
        """ Get the document reference. 
        Raises:
            AttributeError: If docpath is not set.
        """
        return self.docpath.to_docref(db)

    @classmethod
    def load(cls, docpath: str | Path | DocumentReference | DocPath, db: Client) -> "FB":
        if not isinstance(docpath, DocPath):
            docpath = DocPath(docpath)
        return cls(**docpath.to_docref(db).get().to_dict())

    def set(self, db: Client) -> None:
        """ db client is optional when initialized with a DocumentReference.
        Raises:
            AttributeError: If docpath is not set.
        """
        self.docref(db).set(self.to_json(mode='fb'))

    def update(self, db: Client) -> None:
        """ db client is optional when initialized with a DocumentReference.
        Raises:
            AttributeError: If docpath is not set.
        """
        self.docref(db).set(self.to_json(mode='fb'))


    def delete(self, db: Client) -> None:
        """ Delete the document in Firebase. """
