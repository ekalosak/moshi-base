""" A Prompt adapts a ChatMoshi Activity to OpenAI's API.
Key functionality includes:
    - a completion function;
        - maps vocab to logit_bias
        - synchronous retry, backoff, and timeout logic.
        - token counting and logging
    - a templating system; if prompt contains "{{ MY_VAR }}", it will be replaced with the value of {'template': {'my_var': 'my value'}}.
"""
import time

from loguru import logger
import openai
import tiktoken

from moshibase import Message, Role, OPENAI_ROLES, MOSHI_ROLES
from moshibase.prompt import Prompt

from .exceptions import CompletionError

enc: tiktoken.Encoding = None
import dataclasses
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
    logger.log("DETAIL", f"a_f: {available_functions}")
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
    return [res] + _parse_lines(lines[1:], available_functions)

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

    @property
    def model(self) -> str:
        """ e.g. 'gpt-3.5-turbo' """
        return self.mod.value

    def to_json(self) -> dict:
        """ Convert to JSON. """
        return {
            'mod': self.mod.value,
            'msgs': [msg.to_json() for msg in self.msgs],
            'functions': [func.to_json() for func in self.functions],
            'function_call': self.function_call.to_json(),
        }

    @classmethod
    def from_lines(cls, lines: list[str], available_functions: list[Callable]=[]) -> 'Prompt':
        raw_prompt = _parse_lines(lines, available_functions)
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
    def from_file(cls, fp: Path, available_functions: list[Callable]=[]) -> 'Prompt':
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
        return cls.from_lines(lines, available_functions)

def _biases_for_vocab(vocab: list[str], model: str, bias=5.) -> dict[str, float]:
    """Construct the logit_bias completion arg for a given vocab.
    Args:
        - vocab: the vocab to bias completion towards.
        - model: the model to use for encoding.
        - bias: the bias to use for each token.
    """
    if not enc:
        enc = tiktoken.encoding_for_model(model)
    tokens = {}
    with logger.contextualize(model=model):
        for voc in vocab:
            tok = enc.encode(voc)
            tokens[voc] = tok
        logger.debug(f"Tokens: {tokens}")
    tokens = list(tokens.values())
    tokens = [t for toks in tokens for t in toks]
    return {tok: bias for tok in tokens}

def complete(
        prompt: Prompt,
        backoff_count=3,
        vocab: list[str]=[],
        check_user:bool=True,
        **kwargs
    ) -> Message | None:
    """ Returns message with role and content; or None if no completion.
    Args:
        - prompt: the prompt to complete.
        - backoff_count: the number of times to retry the API call before giving up.
        - vocab: the vocab to bias completion towards.
        - check_user: whether to check if the last message is from the user.
        - kwargs: kwargs to pass to openai.ChatCompletion.create
            - n: the number of completions to generate.
            - max_tokens: the maximum number of tokens to generate.
            - stop: the tokens to stop generation at.
            - logit_bias: any additional logit_bias added to the vocab's biases.
            - temperature
            - top_p
            - presence_penalty
            - frequency_penalty
            - best_of
            - and so on: https://platform.openai.com/docs/api-reference/chat/create
    """
    kwargs['n'] = kwargs.get('n', 1)
    kwargs['max_tokens'] = kwargs.get('max_tokens', 128)
    kwargs['stop'] = kwargs.get('stop', ['\n'])  #, '?', '!', '。'])
    if check_user:
        if prompt.msgs[-1].role == 'ast':
            logger.debug("Last message is 'ast', nothing to do.")
            return None
        else:
            logger.debug("Last message is not 'ast', getting completion from model...")
    logit_bias={}
    if vocab:
        logit_bias = _biases_for_vocab(vocab, prompt.model)
    if 'logit_bias' in kwargs:
        logit_bias.update(kwargs['logit_bias'])
    logger.debug(f"Calling OpenAI API with kwargs: {kwargs}")
    logger.debug(f"backoff_count={backoff_count}")
    try:
        response = openai.ChatCompletion.create(
            model=prompt.model,
            messages=[msg.to_json() for msg in prompt.msgs],
            logit_bias=logit_bias,
            **kwargs
        ).to_dict()
    except openai.APIError as e:
        logger.error(f"OpenAI API error: {e}")
    except openai.error.Timeout as e:
        logger.error(f"OpenAI Timeout error: {e}")
    except openai.error.ServiceUnavailableError as e:
        logger.error(f"OpenAI ServiceUnavailableError error: {e}")
    except openai.error.AuthenticationError as e:
        logger.error(f"OpenAI AuthenticationError error: {e}")
        raise e
    except Exception as e:
        logger.error(f"OpenAI unknown error: {type(e)}: {e}")
        raise e
    else:
        logger.info("OpenAI API call succeeded.")
        choices = response.pop('choices')
        usage = response.pop('usage').to_dict()
        msg = None
        with logger.contextualize(**response, usage=usage, kwargs=kwargs):
            logger.debug(f"Total tokens: {usage['total_tokens']}")
            for i, choice in enumerate(choices):
                index = choice.pop('index')
                finish_reason = choice.pop('finish_reason')
                _msg = choice.pop('message')
                role = MOSHI_ROLES[_msg['role']]
                content = _msg['content']
                with logger.contextualize(index=index, finish_reason=finish_reason, role=role):
                    logger.debug(f"Choice {i + 1}: '{content}'")
                    if role != Role.AST:
                        logger.warning(f"Expected assistant response, got {role}.")
                if not msg:
                    logger.debug("Selecting first message")
                    msg = _msg
            logger.debug(f"Completion: {msg['role']:}: '{msg['content']}'")
        return Message.from_json(msg)
    if backoff_count == 0:
        logger.error("OpenAI API error: too many retries.")
        raise CompletionError("Too many retries.")
    logger.info(f"Retrying in 5 seconds... (backoff_count={backoff_count})")
    time.sleep(5)
    return complete(msgs, model, backoff_count=backoff_count - 1, vocab=vocab, check_user=check_user, **kwargs)