"""Models for messages."""
import dataclasses
from enum import Enum

from .audio import AudioStorage
from .versioned import Versioned

ROLES = {
    'ast': 'assistant',
    'sys': 'system',
    'usr': 'user',
ROLES_STR = ', '.join(ROLES.keys())

OPENAI_ROLES = {
    'sys': 'system',
    'usr': 'user',
    'ast': 'assistant',
    'func': 'function',
}
MOSHI_ROLES = {v: k for k, v in OPENAI_ROLES.items()}

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

class PType(str, Enum):
    STRING = 'string'
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    OBJECT = 'object'
    ARRAY = 'array'
    NULL = 'null'

@dataclasses.dataclass
class Property:
    name: str
    ptype: str
    description: str = ""
    enum: list[str] = []

    def to_json(self):
        res = {'name': self.name, 'type': self.ptype}
        if self.description:
            res['description'] = self.description
        if self.enum:
            res['enum'] = self.enum
        return res

@dataclasses.dataclass
class Parameters:
    """ Base class for parameters for a function. """
    properties: list[Property]
    description: str = self.__doc__
    _type = "object"

    def to_json(self):
        ...

@dataclasses.dataclass
class Function:
    """ Base class for functions. """
    name: str
    parameters: Parameters = Parameters()
    description: str = self.__doc__

    def to_openai(self):
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self.parame
        }

    @classmethod
    def from_openai(cls, completion: dict):
        return cls(
            name=completion['name'],
            params=completion['params'],
            body=completion['body'],
        )

@dataclasses.dataclass(kw_only=True)
class Message(Versioned):
    role: Role
    body: str
    audio: AudioStorage | None = None
    translation: str | None = None
    vocab: list[str | dict] = []
    _function: Function | None = None

    def __str__(self):
        """Print message colorized based on message 'role'."""
        role = OPENAI_ROLES[self.role.value]
        color_start = ROLE_COLORS[self.role.value]
        color_end = ROLE_COLORS['reset']
        payload = f"{color_start}[{role}] {self.body}{color_end}"
        print(payload)

    def to_openai(self):
        return {
            'role': self.role.to_openai(),
            'content': self.body,
        }

    @classmethod
    def from_openai(cls, completion: dict):
        return cls(
            role=Role.from_openai(completion['role']),
            body=completion['content'],
        )