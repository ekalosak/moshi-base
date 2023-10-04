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

    def __repr__(self) -> str:
        return f"DocPath({self._path.as_posix()})"

    def __str__(self):
        return self._path.as_posix()
    
    def to_docref(self, db: Client) -> DocumentReference:
        return db.document(self._path.as_posix())

    @property
    def parts(self) -> list[str]:
        return self._path.parts


class Mappable(BaseModel, ABC):

    def to_dict(self, *args, **kwargs) -> dict:
        """ Alias for BaseModel's model_dump. """
        if 'mode' in kwargs:
            logger.warning(f"mode={kwargs['mode']} will be ignored. Overriding to mode=python.")
            kwargs.pop('mode')
        return self.model_dump(*args, mode='python', **kwargs)

    def to_json(self, *args, exclude_none=True, **kwargs) -> dict:
        """ Alias for BaseModel's json-mode model_dump. """
        if 'mode' in kwargs:
            logger.warning(f"mode={kwargs['mode']} will be ignored. Overriding to mode=json.")
            kwargs.pop('mode')
        return self.model_dump(*args, mode='json', exclude_none=exclude_none, **kwargs)

    def to_jsons(self, *args, **kwargs) -> str:
        """ Stringify the json with utils.jsonify. """
        return json.dumps(self.to_json(*args, **kwargs), default=utils.jsonify)


class Versioned(Mappable, ABC):
    base_version: str = __version__

    @field_validator('base_version')
    def check_version(cls, v):
        if v != __version__:
            logger.warning(f"Version mismatch: got {v} != base {__version__}")
        return v


class FB(Versioned, ABC):

    @abstractproperty
    def docpath(self) -> DocPath:
        """ The path to the document in Firestore. """
        ...

    @classmethod
    def _kwargs_from_docpath(cls, docpath: DocPath) -> dict:
        """ Get kwargs from the docpath. For example, /users/<uid> should return {'uid': <uid>}. """
        return {}

    def to_fb(self, *args, **kwargs) -> dict:
        """ Coerce self.to_json output into the format expected by Firestore.
        Examples:
            {'foo': {'bar': 1}} -> {'foo.bar': 1}
        """
        return utils.flatten(self.to_json(*args, **kwargs))

    def docref(self, db: Client) -> DocumentReference:
        """ Get the document reference. 
        Raises:
            AttributeError: If docpath is not set.
        """
        docpath = self.docpath
        for part in docpath._path.parts:
            if part == 'None' or not part:
                raise ValueError(f"Invalid path, no empty parts allowed: {docpath}")
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
        if not ds.exists:
            raise ValueError(f"Document {docpath} does not exist in Firebase.")
        dat = ds.to_dict()
        with logger.contextualize(dbpath=docpath, dbproject=db.project):
            logger.debug(f"Got data from Fb: {dat}")
            if dbpath_kwargs := cls._kwargs_from_docpath(docpath):
                dat.update(dbpath_kwargs)
                logger.debug(f"Updated with kwargs derived from {docpath}: {dat}")
        return cls(**dat)

    def create(self, db: Client, **kwargs) -> None:
        """ Create the document in Firestore if it doesn't exist.
        Raises:
            AttributeError: If docpath is not set.
            AlreadyExists: If the document already exists.
        """
        return self.docref(db).create(self.to_json(), **kwargs)

    def set(self, db: Client, **kwargs):
        """ Set the document in FirestoreFirebase.
        Raises:
            AttributeError: If docpath is not set.
        """
        return self.docref(db).set(self.to_json(), **kwargs)

    def merge(self, db: Client, **kwargs):
        """ Set the document in Firestore using the merge option.
        Raises:
            AttributeError: If docpath is not set.
        """
        if kwargs.get('merge') is False:
            logger.warning("merge=False is not allowed. Overriding to merge=True.")
        kwargs['merge'] = True
        return self.docref(db).set(self.to_json(), **kwargs)

    def update(self, db: Client, **kwargs):
        """ Update the document in Firestore.
        Raises:
            AttributeError: If docpath is not set.
        """
        return self.docref(db).update(self.to_fb(), **kwargs)

    def delete(self, db: Client, **kwargs) -> None:
        """ Delete the document in Firestore. """
        return self.docref(db).delete(**kwargs)
