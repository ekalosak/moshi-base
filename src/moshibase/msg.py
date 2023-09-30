"""Models for messages."""
import dataclasses
from enum import Enum

from .audio import AudioStorage
from .versioned import Versioned

OPENAI_ROLES = {
    'sys': 'system',
    'usr': 'user',
    'ast': 'assistant',
    'func': 'function',
}
MOSHI_ROLES = {v: k for k, v in OPENAI_ROLES.items()}

# Color codes for printing messages.
ROLE_COLORS = {
    'ast': '\033[95m', # magenta
    'sys': '\033[93m', # yellow
    'usr': '\033[96m', # cyan
    'func': '\033[92m', # green
    'reset': '\033[0m',  # back to default
}

class Role(str, Enum):
    SYS = 'sys'
    USR = 'usr'
    AST = 'ast'
    FUNC = 'func'

    def to_openai(self):
        return OPENAI_ROLES[self.value]

    @classmethod
    def from_openai(cls, role: str):
        return cls(MOSHI_ROLES[role])

@dataclasses.dataclass(kw_only=True)
class Message(Versioned):
    role: Role
    body: str
    audio: AudioStorage | None = None
    translation: str | None = None
    vocab: list[str | dict] = []

    def __str__(self):
        """Print message colorized based on message 'role'."""
        role = OPENAI_ROLES[self.role.value]
        color_start = ROLE_COLORS[self.role.value]
        color_end = ROLE_COLORS['reset']
        payload = f"{color_start}[{role}] {self.body}{color_end}"
        print(payload)

    def to_json(self):
        return {
            'role': self.role.to_openai(),
            'content': self.body,
        }

    @classmethod
    def from_json(cls, completion: dict):
        return cls(
            role=Role.from_openai(completion['role']),
            body=completion['content'],
        )