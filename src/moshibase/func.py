""" Functions for OpenAI models. https://platform.openai.com/docs/api-reference/chat/create#functions """
import dataclasses
from enum import Enum, EnumType
import inspect
from typing import Callable

class PType(str, Enum):
    """ Types allowed in functions. """
    STRING = 'string'
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    OBJECT = 'object'
    ARRAY = 'array'
    NULL = 'null'

    @classmethod
    def from_annotation(cls, annotation: type):
        """ Get PType from type annotation. """
        if annotation == str:
            return cls.STRING
        elif isinstance(annotation, EnumType):
            return cls.STRING
        elif annotation == int or annotation == float:
            return cls.NUMBER
        elif annotation == bool:
            return cls.BOOLEAN
        elif annotation == list:
            return cls.ARRAY
        elif annotation == dict:
            return cls.OBJECT
        else:
            raise ValueError(f"Annotation has no match in JSON parameter types: {annotation}")

@dataclasses.dataclass
class FuncCall:
    """ Controls how model calls functions. """
    func: str = "auto"

    def to_json(self):
        if self.func in {'auto', 'none'}:
            return self.func
        else:
            return {'name': self.func}
        

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

    @classmethod
    def from_dict(cls, d: dict):
        """ Create a Property from a dict. """
        ptype = PType(d['type'])
        description = d.get('description', '')
        enum = d.get('enum', [])
        return cls(ptype, description, enum)

def _parse_docstring_description(docstring: str) -> str:
    """ Parse docstring for the main description of the function.
    From a Google-style Python docstring, get the top-level description.
    For example, from:
    '''Example function. Does a thing.
    Args:
        arg1: The first argument.
        arg2: The second argument.
    '''
    Return 'Example function. Does a thing.'
    """
    if not docstring:
        return ""
    lines = docstring.splitlines()
    description = ""
    for line in lines:
        if not line.strip():
            return description
        description += line.strip() + " "
    return description.strip()

def _parse_docstring_arg(docstring: str, name: str) -> str:
    """ Parse docstring for property description.
    From a Google-style Python docstring, get the text corresponding to the argument name.
    For example, from:
    '''Example function. Does a thing.
    Args:
        arg1: The first argument.
        arg2: The second argument.
    '''
    If name='arg1', return 'The first argument.'
    """
    if not docstring:
        return ""
    lines = docstring.splitlines()
    for line in lines:
        if line.strip().startswith(name):
            return line.split(':')[-1].strip()
    return ""

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

    @classmethod
    def from_dict(cls, d: dict):
        """ Create a Parameters from a dict. """
        properties = {
            name: Property.from_dict(prop)
            for name, prop in d['properties'].items()
        }
        required = d.get('required', [])
        return cls(properties, required)

    @classmethod
    def from_callable(cls, func: callable):
        """ Create a Parameters from a callable. """
        sig = inspect.signature(func)
        properties = {}
        required = []
        for name, param in sig.parameters.items():
            if param.default == inspect.Parameter.empty:
                required.append(name)
            if param.annotation == inspect.Parameter.empty:
                raise ValueError(f"Parameter '{name}' has no type annotation.")
            ptype = PType.from_annotation(param.annotation)
            enums = []
            if isinstance(param.annotation, EnumType):
                enums = [e.value for e in param.annotation]
            prop_description = _parse_docstring_arg(func.__doc__, name)
            properties[name] = Property(ptype, description=prop_description, enum=enums)
        return cls(properties, required)
            

@dataclasses.dataclass
class Function:
    """ Base class for OpenAI functions. """
    name: str
    func: Callable
    parameters: Parameters = dataclasses.field(default_factory=Parameters)
    description: str = ""

    def to_json(self):
        res = {'name': self.name, 'parameters': self.parameters.to_json()}
        if self.description:
            res['description'] = self.description
        return res

    @classmethod
    def from_callable(cls, func: callable):
        """ Create a Function from a callable. """
        name = func.__name__
        description = _parse_docstring_description(func.__doc__)
        parameters = Parameters.from_callable(func)
        return cls(name, func, parameters, description)