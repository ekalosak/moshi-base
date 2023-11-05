"""Models for messages."""
from datetime import datetime
from enum import Enum

from pydantic import Field
from loguru import logger

from . import utils
from .audio import AudioStorage
from .grade import Scores
from .log import LOG_COLORIZE
from .storage import Mappable
from .vocab import MsgV

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

class Message(Mappable):
    created_at: datetime = Field(default_factory=utils.utcnow)
    role: Role
    body: str
    audio: AudioStorage = None
    translation: str = None
    vocab: dict[str, dict[str, str]] = None
    grammar: str = None
    score: Scores = None

    def __init__(self, role: Role, body: str, **kwargs):
        logger.opt(depth=1).debug("DEPRECATION NOTICE: migrate to message(role, body, **kwargs) function. REASON: docstring popup in vscode is not the auto-generated one from pydantic.")
        super().__init__(role=role, body=body, **kwargs)

    def __str__(self):
        """Print message colorized based on message 'role'."""
        role = self.role.value
        res = f"[{role}] {self.body}"
        if LOG_COLORIZE:
            color_start = ROLE_COLORS[self.role.value]
            color_end = ROLE_COLORS['reset']
            res = f"{color_start}{res}{color_end}"
        return res

    @property
    def mvs(self) -> list[MsgV]:
        """ Get the MsgV values for the message's vocab. """
        if self.vocab:
            return [MsgV(term=k, **v) for k, v in self.vocab.items()]
        return []

    @classmethod
    def from_string(cls, body: str, role: Role=Role.USR):
        return cls(role, body)

    def to_openai(self):
        return {
            'role': self.role.to_json(),
            'content': self.body,
        }

    def to_dict(self, exclude_none=True, **kwargs):
        """ Convert to a dictionary using the BaseModel model_dump method.
        Args:
            exclude_none: If True, exclude fields with None values.
            kwargs: Additional arguments to pass to model_dump_json.
        """
        return self.model_dump(exclude_none=exclude_none, **kwargs)

    def to_json(self, exclude_none=True, **kwargs):
        """ Convert to JSON using self.to_dict(mode='json')
        Args:
            exclude_none: If True, exclude fields with None values.
            kwargs: Additional arguments to pass to model_dump_json.
        """
        if 'mode' in kwargs:
            logger.warning("Overriding 'mode' argument to 'json'.")
        kwargs['mode'] = 'json'
        return self.to_dict(exclude_none=exclude_none, **kwargs)

    @classmethod
    def from_openai(cls, completion: dict):
        return cls(
            role=Role.from_json(completion['role']),
            body=completion['content'],
        )

def message(role: str, body: str, **kwargs) -> Message:
    """Conveinece function to create a Message from a role and body."""
    return Message(role=Role(role), body=body, **kwargs)