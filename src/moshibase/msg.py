"""Models for messages."""
from enum import Enum

from .audio import AudioStorage
from .versioned import Versioned

OPENAI_ROLES = {
    "sys": "system",
    "usr": "user",
    "ast": "assistant",
}
MOSHI_ROLES = {v: k for k, v in OPENAI_ROLES.items()}

class Role(str, Enum):
    SYS = "sys"
    USR = "usr"
    AST = "ast"

    def to_openai(self):
        return OPENAI_ROLES[self.value]

    @classmethod
    def from_openai(cls, role: str):
        return cls(MOSHI_ROLES[role])

class Message(Versioned):
    role: Role
    body: str
    audio: AudioStorage | None = None
    translation: str | None = None