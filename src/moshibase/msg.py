"""Models for messages."""
from enum import Enum

from .audio import AudioStorage
from .versioned import Versioned

class Role(str, Enum):
    SYS = "system"
    USR = "user"
    AST = "assistant"

class Message(Versioned):
    role: Role
    body: str
    audio: AudioStorage | None = None
    translation: str | None = None