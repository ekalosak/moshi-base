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
        # edge cases
        if not any(msg.mvs for msg in tra.msgs):
            logger.debug("Transcript has no vocab. Not updating user vocabulary.")
            return
        # get doc
        docr = self.vocabdocpath.to_docref(db)
        doc = docr.get()
        if not doc.exists:
            dat = {}
        else:
            dat = doc.to_dict()
        # parse doc data into all user's vocab
        usgvoc = {k: UsageV(**v) for k, v in dat.items()}
        # update usage of user's vocab
        total_new = 0
        update = {}
        for mid, msg in tra.messages.items():
            if msg.role != 'usr':
                continue
            new_in_msg = 0
            for msgv in msg.mvs:
                usg = Usage(tid=tra.tid, mid=mid)
                if msgv.term in usgvoc:
                    logger.debug(f"User used '{msgv.term}' again.")
                    usgvoc[msgv.term].add_usage(usg)
                    update[msgv.term]: UsageV = usgvoc[msgv.term]
                else:
                    logger.debug(f"User used '{msgv.term}' for the first time.")
                    usgvoc[msgv.term] = UsageV(term=msgv.term, usgs=[usg], first=msg.created_at, last=msg.created_at)
                    new_in_msg += 1
            if new_in_msg > 0:
                with logger.contextualize(mid=mid, tid=tra.tid):
                    logger.debug(f"User used {new_in_msg} new terms in this message.")
                total_new += new_in_msg
        if total_new > 0:
            with logger.contextualize(tid=tra.tid):
                logger.info(f"User used {total_new} new terms in this session.")
        pld = {k: v.model_dump(exclude_none=True) for k, v in usgvoc.items()}
        docr.set(pld, merge=True)
        with logger.contextualize(uid=self.uid, tid=tra.tid):
            logger.info("Updated user vocabulary.")