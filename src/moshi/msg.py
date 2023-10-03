"""Models for messages."""
import dataclasses
from enum import Enum

from .audio import AudioStorage

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

    @property
    def color(self):
        return ROLE_COLORS[self.value]

    def to_json(self):
        """ Convert to OpenAI role. """
        return OPENAI_ROLES[self.value]

    @classmethod
    def from_json(cls, role: str):
        return cls(MOSHI_ROLES[role])

@dataclasses.dataclass
class Message:
    role: Role
    body: str
    audio: AudioStorage | None = None
    translation: str | None = None
    vocab: list[str | dict] = dataclasses.field(default_factory=list)

    def __str__(self):
        """Print message colorized based on message 'role'."""
        role = self.role.value
        color_start = ROLE_COLORS[self.role.value]
        color_end = ROLE_COLORS['reset']
        return f"{color_start}[{role}] {self.body}{color_end}"

    def to_json(self):
        return {
            'role': self.role.to_json(),
            'content': self.body,
        }

    @classmethod
    def from_json(cls, completion: dict):
        return cls(
            role=Role.from_json(completion['role']),
            body=completion['content'],
        )