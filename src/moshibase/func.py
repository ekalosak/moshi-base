import dataclasses
from enum import Enum

class PType(str, Enum):
    """ Types allowed in functions. """
    STRING = 'string'
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    OBJECT = 'object'
    ARRAY = 'array'
    NULL = 'null'

@dataclasses.dataclass
class Property:
    """ Arguments for functions. """
    ptype: PType
    description: str = ""
    enum: list[str] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        if self.enum and self.ptype != PType.STRING:
            raise ValueError("Enum is only valid for string properties.")

    def to_json(self):
        """ Doesn't include name. """
        res = {'type': self.ptype.value}
        if self.description:
            res['description'] = self.description
        if self.enum:
            res['enum'] = self.enum
        return res

@dataclasses.dataclass
class Parameters:
    """ List of function arguments (properties) and which are required. """
    properties: dict[str, Property] = dataclasses.field(default_factory=dict)
    required: list[str] = dataclasses.field(default_factory=list)
    _type = "object"

    def __post_init__(self):
        if self.required:
            for req in self.required:
                if req not in self.properties:
                    raise ValueError(f"Required property '{req}' not found in properties.")

    def to_json(self):
        res = {'type': self._type}
        if self.properties:
            res['properties'] = {k: v.to_json() for k, v in self.properties.items()}
        else:
            res['properties'] = {}
        if self.required:
            res['required'] = self.required
        return res

@dataclasses.dataclass
class Function:
    """ Base class for OpenAI functions. """
    name: str
    parameters: Parameters = dataclasses.field(default_factory=Parameters)
    description: str = ""

    def to_json(self):
        res = {'name': self.name, 'parameters': self.parameters.to_json()}
        if self.description:
            res['description'] = self.description
        return res