from pathlib import Path
from typing import Callable

import pytest

from moshi import Prompt, model, Message, Role, Function, Parameters
from moshi.prompt import _parse_lines, _get_function, _load_lines, Prompt

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
    expected_messages = [
        Message(Role.SYS, "Only use the functions you have been provided with."),
        function,
        Message(Role.SYS, "Be polite."),
        Message(Role.USR, "Hello."),
    ]
    for pmsg, emsg in zip(prompt_contents, expected_messages):
        if isinstance(emsg, Function):
            assert pmsg.name == emsg.name
        else:
            assert pmsg.role == emsg.role
            assert pmsg.body == emsg.body

def test_from_file_forgot_functions(prompt: Prompt, prompt_file: Path):
    with pytest.raises(ValueError):
        Prompt.from_file(prompt_file)

def test_from_file(prompt: Prompt, prompt_file: Path, get_topic: Callable, get_name: Callable):
    prompt = Prompt.from_file(prompt_file, [get_topic, get_name])
    assert prompt.mod == model.ChatM.GPT35TURBO
    expected_messages = [
        Message(Role.SYS, "Only use the functions you have been provided with."),
        Message(Role.SYS, "Be polite."),
        Message(Role.USR, "Hello."),
    ]
    for pmsg, emsg in zip(prompt.msgs, expected_messages):
        if isinstance(emsg, Function):
            assert pmsg.name == emsg.name
        else:
            assert pmsg.role == emsg.role
            assert pmsg.body == emsg.body
    assert len(prompt.functions) == 1
    func = prompt.functions[0]
    assert isinstance(func, Function)
    assert func.to_json() == Function(
        name="get_topic",
        func=lambda x: x,
        description= "Come up with a topic to talk about.",
    ).to_json()
    assert prompt.function_call == None

def test_template_happy():
    msg = Message('sys', "Hello, {{NAME}}!")
    pro = Prompt(msgs=[msg])
    pro.template(NAME="World")
    assert pro.msgs[0].body == "Hello, World!"

def test_template_fail_case():
    msg = Message('sys', "Hello, {{NAME}}!")
    pro = Prompt(msgs=[msg])
    with pytest.raises(ValueError):
        pro.template(name="World")

def test_template_fail_whitespace():
    msg = Message('sys', "Hello, {{ NAME }}!")
    pro = Prompt(msgs=[msg])
    with pytest.raises(ValueError):
        pro.template(name="World")

def test_template_fail_dne():
    msg = Message('sys', "Hello, World!")
    pro = Prompt(msgs=[msg])
    with pytest.raises(ValueError):
        pro.template(name="World")