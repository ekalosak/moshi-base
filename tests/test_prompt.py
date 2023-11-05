from pathlib import Path
from typing import Callable

import pytest

from moshi import Prompt, model, Role, Function, Parameters, message
from moshi.prompt import _concatenate_multiline, _parse_lines, _get_function, _load_lines, Prompt
from moshi import utils

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
        message(Role.SYS, "Only use the functions you have been provided with."),
        function,
        message(Role.SYS, "Be polite."),
        message(Role.USR, "Hello."),
    ]
    for pmsg, emsg in zip(prompt_contents, expected_messages):
        if isinstance(emsg, Function):
            assert pmsg.name == emsg.name
        else:
            assert pmsg.role == emsg.role
            assert pmsg.body == emsg.body

def test_from_lines():
    lines = ["sys: Hello\\", "world!"]
    pro = Prompt.from_lines(lines)
    assert pro.msgs[0].role == Role.SYS
    assert len(pro.msgs) == 1
    assert pro.msgs[0].body == "Hello\nworld!"

def test_from_file_forgot_functions(prompt: Prompt, prompt_file: Path):
    with pytest.raises(ValueError):
        Prompt.from_file(prompt_file)

def test_from_file(prompt: Prompt, prompt_file: Path, get_topic: Callable, get_name: Callable):
    prompt = Prompt.from_file(prompt_file, [get_topic, get_name])
    assert prompt.mod == model.ChatM.GPT35TURBO
    expected_messages = [
        message(Role.SYS, "Only use the functions you have been provided with."),
        message(Role.SYS, "Be polite."),
        message(Role.USR, "Hello."),
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

@pytest.mark.parametrize('pld', ["World", 123])
def test_template_happy(pld: str):
    msg = message('sys', "Hello, {{NAME}}!")
    pro = Prompt(msgs=[msg])
    pro.template(NAME=pld)
    assert pro.msgs[0].body == f"Hello, {pld}!"

def test_template_fail_case():
    msg = message('sys', "Hello, {{NAME}}!")
    pro = Prompt(msgs=[msg])
    with pytest.raises(ValueError):
        pro.template(name="World")

def test_template_fail_whitespace():
    msg = message('sys', "Hello, {{ NAME }}!")
    pro = Prompt(msgs=[msg])
    with pytest.raises(ValueError):
        pro.template(name="World")

def test_template_fail_dne():
    msg = message('sys', "Hello, World!")
    pro = Prompt(msgs=[msg])
    with pytest.raises(ValueError):
        pro.template(name="World")

@pytest.mark.gcp
def test_translate():
    msg = message('sys', "Hello, World!")
    pro = Prompt(msgs=[msg])
    print(f"Before: {pro}")
    pro.translate("es-MX")
    print(f"After: {pro}")
    assert utils.similar(pro.msgs[0].body, "¡Hola Mundo!") > 0.75

def test_concatenate_multiline_empty():
    lines = []
    assert _concatenate_multiline(lines) == []

def test_concatenate_multiline_single_line():
    lines = ["Hello, world!"]
    assert _concatenate_multiline(lines) == ["Hello, world!"]

def test_concatenate_multiline_single_line_backslash():
    lines = ["Hello, world!\\"]
    with pytest.raises(ValueError):
        _concatenate_multiline(lines)

def test_concatenate_multiline_multiple_lines():
    lines = [
        "Hello,",
        "world!",
    ]
    assert _concatenate_multiline(lines) == ["Hello,",  "world!"]

def test_concatenate_multiline_multiple_lines_backslash():
    lines = [
        "Hello,",
        "world!\\",
        "How are you?",
    ]
    assert _concatenate_multiline(lines) == ["Hello,", "world!\nHow are you?"]

def test_concatenate_multiline_multiple_lines_backslash_multiple():
    lines = [
        "Hello,",
        "world!\\",
        "How are you?\\",
        "I'm doing well, thanks for asking.",
    ]
    assert _concatenate_multiline(lines) == ["Hello,", "world!\nHow are you?\nI'm doing well, thanks for asking."]