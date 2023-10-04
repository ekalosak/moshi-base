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

class DocPath:
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
    def read(cls, docpath: DocPath, db: Client) -> "FB":
        """ Read the document from Firestore.
        Raises:
            ValueError: If the document does not exist.
        """
        if not isinstance(docpath, DocPath):
            docpath = DocPath(docpath)
        dr = docpath.to_docref(db)
        ds = dr.get()
        dat = ds.to_dict()
        logger.debug(f"Got data from Fb: {dat}")
        if dat is None:
            raise ValueError(f"Document {docpath} does not exist in Firebase.")
        return cls(**dat)

    def create(self, db: Client, **kwargs) -> None:
        """ Create the document in Firestore if it doesn't exist.
        Raises:
            AttributeError: If docpath is not set.
            AlreadyExists: If the document already exists.
        """
        self.docref(db).create(self.to_json(mode='fb'), **kwargs)

    def set(self, db: Client, **kwargs) -> None:
        """ Set the document in FirestoreFirebase.
        Raises:
            AttributeError: If docpath is not set.
        """
        self.docref(db).set(self.to_json(mode='fb'), **kwargs)

    def update(self, db: Client, **kwargs) -> None:
        """ Update the document in Firestore.
        Raises:
            AttributeError: If docpath is not set.
        """
        return self.docref(db).set(self.to_json(mode='fb'), **kwargs)

    def delete(self, db: Client, **kwargs) -> None:
        """ Delete the document in Firestore. """
        return self.docref(db).delete(**kwargs)
