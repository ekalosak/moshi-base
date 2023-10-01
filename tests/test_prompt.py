from pathlib import Path

import pytest

from moshibase import Prompt, model, Message, Role, Function, FuncCall
from moshibase.prompt import _parse_func, _parse_lines, _parse_parameters, load_lines


@pytest.fixture
def prompt():
    return Prompt(
        mod=model.ChatM.GPT35TURBO,
        msgs=[
            Message(Role.SYS, "Only use the functions you have been provided with."),
            Message(Role.SYS, "Be polite."),
            Message(Role.USR, "Hello."),
        ],
        functions=[
            Function(
                name="get_topic",
                description="Get a topic to talk about.",
            ),
        ],
        function_call=FuncCall("get_topic"),
    )

@pytest.fixture
def prompt_file():
    return Path(__file__).parent / "test_prompt.txt"


def test_from_file(prompt, prompt_file):
    prompt = Prompt.from_file(prompt_file)
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
        description="Get a topic to talk about.",
    ).to_json()
    assert prompt.function_call == FuncCall("auto")


def test_parse_func():
    lines = [
        "    name: get_topic",
        "    description: Get a topic to talk about.",
        "    parameters: {}",
    ]
    result, _ = _parse_func(lines)
    assert result == Function(
        name="get_topic",
        description="Get a topic to talk about.",
    )

def test_parse_func_no_params():
    lines = [
        "    name: get_topic",
        "    description: Get a topic to talk about.",
    ]
    result, _ = _parse_func(lines)
    assert result == Function(
        name="get_topic",
        description="Get a topic to talk about.",
    )

@pytest.mark.skip(reason="Not implemented yet.")
def test_parse_parameters():
    lines = [
        "parameters:",
        "    properties:",
        "        topic:",
        "            type: string",
        "            description: The topic to talk about.",
        "    required:",
        "        - topic",
    ]
    result, num_lines = _parse_parameters(lines)
    assert result == {
        "topic": {
            "type": "string",
            "description": "The topic to talk about.",
        }
    }
    assert num_lines == 7