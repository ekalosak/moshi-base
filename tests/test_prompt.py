from pathlib import Path
from typing import Callable

import pytest

from moshi import Prompt, model, Message, Role, Function, FuncCall, Parameters
from moshi.prompt import _parse_lines, _get_function, _load_lines, Prompt

@pytest.fixture
def function(get_topic: Callable):
    return Function(
        name="get_topic",
        func=get_topic,
        description= "Come up with a topic to talk about.",
    )

@pytest.fixture
def prompt(function):
    return Prompt(
        mod=model.ChatM.GPT35TURBO,
        msgs=[
            Message(Role.SYS, "Only use the functions you have been provided with."),
            Message(Role.SYS, "Be polite."),
            Message(Role.USR, "Hello."),
        ],
        functions=[function],
        function_call=FuncCall("get_topic"),
    )

@pytest.fixture
def prompt_file():
    return Path(__file__).parent / "test_prompt.txt"

def test_load_lines(prompt_file: Path):
    lines = _load_lines(prompt_file)
    for line in lines:
        assert '#' not in line, "Failed to remove comments from lines."

def test_get_function(get_topic: Callable):
    func = _get_function("get_topic", [get_topic])
    assert func.name == "get_topic"
    assert func.description == "Come up with a topic to talk about."
    assert func.parameters == Parameters()

def test_parse_lines(prompt_file: Path, get_topic: Callable, function: Function):
    lines = _load_lines(prompt_file)
    prompt_contents = _parse_lines(lines, [get_topic])
    assert prompt_contents == [
        Message(Role.SYS, "Only use the functions you have been provided with."),
        function,
        Message(Role.SYS, "Be polite."),
        Message(Role.USR, "Hello."),
    ]

def test_from_file_forgot_functions(prompt: Prompt, prompt_file: Path):
    with pytest.raises(ValueError):
        Prompt.from_file(prompt_file)

def test_from_file(prompt: Prompt, prompt_file: Path, get_topic: Callable, get_name: Callable):
    prompt = Prompt.from_file(prompt_file, [get_topic, get_name])
    assert prompt.mod == model.ChatM.GPT35TURBO
    assert prompt.msgs == [
        Message(Role.SYS, "Only use the functions you have been provided with."),
        Message(Role.SYS, "Be polite."),
        Message(Role.USR, "Hello."),
    ]
    assert len(prompt.functions) == 1
    func = prompt.functions[0]
    assert isinstance(func, Function)
    assert func.to_json() == Function(
        name="get_topic",
        func=lambda x: x,
        description= "Come up with a topic to talk about.",
    ).to_json()
    assert prompt.function_call == None