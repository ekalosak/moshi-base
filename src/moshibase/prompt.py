import dataclasses
import json
from pathlib import Path
from typing import Callable

from loguru import logger

from .msg import Message, Role
from .func import Function, FuncCall
from . import model

def _get_function(func_name: str, available_functions: list[Callable]) -> Function:
    """ Get a function from a list of available functions. """
    for func in available_functions:
        if func.__name__ == func_name:
            return Function.from_callable(func)
    raise ValueError(f"Function {func_name} not found in available functions.")

def _parse_lines(lines: list[str], available_functions: list[Callable]=[]) -> list[Function | Message | model.ChatM]:
    """ Parse the next function or message from a list of lines. """
    if not lines:
        return []
    line = lines[0]
    parts = line.split(':')
    if parts[0].strip().lower() in model.ChatM.__members__:
        res = model.ChatM(parts[0].strip().lower())
    else:
        role = Role(parts[0].strip().lower())
        if role == Role.FUNC:
            assert len(parts) == 2
            func_name = parts[1].strip()
            res = _get_function(func_name, available_functions)
        else:
            text = ':'.join(parts[1:])
            text = text.strip()
            res = Message(role, text)
    return [res] + _parse_lines(lines[1:])

def _load_lines(fp: Path) -> list[str]:
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
        lines = _load_lines(fp)
        return cls.from_lines(lines)