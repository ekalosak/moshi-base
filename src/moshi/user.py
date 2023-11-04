"""This module provides a datamodel of the user profile."""
from datetime import datetime

from google.cloud.firestore import Client
from loguru import logger
from pydantic import BaseModel, Field

from . import utils
from .storage import FB, DocPath
from .transcript import Transcript
from .vocab import UsageV, MsgV
from .vocab.usage import Usage

class Streak(BaseModel):
    count: int=0
    last: datetime=Field(None, help="Last time user completed a lesson.")
    tid: str=Field(None, help="Last transcript id.")

class User(FB):
    """Models the user profile."""
    uid: str
    name: str
    language: str
    native_language: str
    streak: Streak=Field(default_factory=Streak)
    created_at: datetime=Field(default_factory=utils.utcnow)

    @property
    def bcp47(self) -> str:
        return self.language

    @property
    def docpath(self) -> DocPath:
        return DocPath(f'users/{self.uid}')

    @property
    def vocabdocpath(self) -> DocPath:
        return DocPath(f'users/{self.uid}/vocab/{self.language}')

    def get_vocab(self, db: Client) -> dict[str, UsageV] | None:
        """Get the user's vocabulary."""
        doc = self.vocabdocpath.to_docref(db).get()
        if not doc.exists:
            logger.debug(f"User {self.uid} has no vocabulary yet.")
            return None
        dat = doc.to_dict()
        logger.debug(f"User vocabulary found. len(doc.to_dict())={len(dat)}")
        return {k: UsageV(**v, term=k) for k, v in dat.items()}

    @classmethod
    def from_uid(cls, uid: str, db: Client) -> 'User':
        return super().read(DocPath(f'users/{uid}'), db)

    def update_vocab(self, tra: Transcript, db: Client):
        """ Extract the vocab from the transcript and update the user's vocab doc. """
        if not any(msg.mvs for msg in tra.messages):
            logger.debug("Transcript has no vocab. Not updating user vocabulary.")
            return
        docr = self.vocabdocpath.to_docref(db)
        doc = docr.get()
        if not doc.exists:
            usgvoc = {}
        else:
            usgvoc = doc.to_dict()
        # print(f"before update: usgvoc={usgvoc}")
        usgvoc = {k: UsageV(**v) for k, v in usgvoc.items()}  # all user's vocab
        total_new = 0
        for msg in tra.messages:
            # print(f'msg={msg}')
            # print(f'msg dict: {msg.model_dump()}')
            new_in_msg = 0
            for msgv in msg.mvs:
                usg = Usage(tid=tra.tid, mid=msg.mid)
                # print(f'usg={usg}')
                if msgv.term in usgvoc:
                    # print('not new, updating...')
                    usgvoc[msgv.term].add_usage(Usage(tid=tra.tid, mid=msg.mid))
                else:
                    # print('new, creating...')
                    usgvoc[msgv.term] = UsageV(term=msgv.term, usgs=[usg], first=msg.created_at, last=msg.created_at)
                    logger.debug(f"User used '{msgv.term}' for the first time.")
                    new_in_msg += 1
                # print(f'after update/create: usgvoc[{msgv.term}]={usgvoc[msgv.term]}')
            if new_in_msg > 0:
                logger.debug(f"User used {new_in_msg} new terms in a message")
                total_new += new_in_msg
        if total_new > 0:
            logger.info(f"User used {total_new} new terms in this session.")
        # print(f"after all terms updated: usgvoc={usgvoc}")
        pld = {k: v.model_dump(exclude_none=True, exclude=['term']) for k, v in usgvoc.items()}
        docr.set(pld, merge=True)
        logger.info("Updated user vocabulary.")