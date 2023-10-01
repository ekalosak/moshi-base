import dataclasses
import json
from pathlib import Path

from loguru import logger

from .msg import Message, Role
from .func import Function, FuncCall, Parameters
from . import model

def _parse_parameters(params: str) -> Parameters:
    """ Parse a string containing a json object representing parameters. """
    params = params.strip()
    params = json.loads(params)
    logger.debug(f"params: {params}")
    if not params:
        return Parameters()
    return Parameters.from_dict(params)

def _parse_func(lines: list[str]) -> tuple[Function, int]:
    """ Parse a multi-line block containing a function specification.
    Note that parameters json must be one line valid json.
    Returns:
        - Function
        - number of lines parsed
    """
    relevant_lines = []
    for line in lines:
        if any(line.startswith(role.value) for role in Role):
            break
        relevant_lines.append(line)
    logger.debug(f"relevant_lines: {relevant_lines}")
    kwargs = {
        parts[0].strip(): parts[1].strip()
        for parts in [
            line.split(':')
            for line in relevant_lines
        ]
    }
    logger.debug(f"kwargs: {kwargs}")
    if 'parameters' in kwargs:
        kwargs['parameters'] = _parse_parameters(kwargs['parameters'])
    return Function(**kwargs), len(relevant_lines)
    

def _parse_lines(lines: list[str]) -> list[Function | Message | model.ChatM]:
    """ Parse the next function or message from a list of lines. """
    if not lines:
        return []
    line = lines[0]
    parts = line.split(':')
    if parts[0].strip().lower() in model.ChatM.__members__:
        return [model.ChatM(parts[0].strip().lower())] + _parse_lines(lines[1:])
    role = Role(parts[0].strip().lower())
    if role == Role.FUNC:
        func, i = _parse_func(lines[1:])
        logger.debug(f"func: {func}")
        logger.debug(f"i: {i}")
        logger.debug(f"remaining lines: {lines[i:]}")
        return [func] + _parse_lines(lines[i + 1:])
    else:
        text = ':'.join(parts[1:])
        text = text.strip()
        return [Message(role, text)] + _parse_lines(lines[1:])

def load_lines(fp: Path) -> list[str]:
    """ load lines that aren't commented out with '#' """
    with open(fp, 'r') as f:
        _lines = f.readlines()
    lines = []
    for line in _lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            continue
        lines.append(line)
    return lines

@dataclasses.dataclass
class Prompt:
    """A prompt for OpenAI's API."""
    mod: model.ChatM = model.ChatM.GPT35TURBO
    msgs: list[Message] = dataclasses.field(default_factory=list)
    functions: list[Function] = dataclasses.field(default_factory=list)
    function_call: FuncCall = dataclasses.field(default_factory=FuncCall)

    @classmethod
    def from_lines(cls, lines: list[str]) -> 'Prompt':
        raw_prompt = _parse_lines(lines)
        mod = None
        msgs = []
        funcs = [] 
        for item in raw_prompt:
            if isinstance(item, model.ChatM):
                mod = item
            elif isinstance(item, Message):
                msgs.append(item)
            elif isinstance(item, Function):
                funcs.append(item)
            else:
                raise ValueError(f"Unknown item type: {item}")
        kwargs = {
            'msgs': msgs,
            'functions': funcs,
        }
        if mod:
            kwargs['mod'] = mod
        return cls(**kwargs)

    @classmethod
    def from_file(cls, fp: Path) -> 'Prompt':
        """Parse a prompt file in this format:
        ```
        sys: Only use the functions you have been provided with.
        func:
            name: get_topic
            description: Get a topic to talk about.
            parameters: {}
        sys: Be polite.
        usr: Hello, how are you?
        ```
        Lines starting with '#' are ignored.
        """
        lines = load_lines(fp)
        return cls.from_lines(lines)