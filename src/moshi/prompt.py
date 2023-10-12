""" A Prompt adapts a ChatMoshi Activity to OpenAI's API.
Key functionality includes:
    - a completion function;
        - maps vocab to logit_bias
        - synchronous retry, backoff, and timeout logic.
        - token counting and logging
    - a templating system; if prompt contains "{{ MY_VAR }}", it will be replaced with the value of {'template': {'my_var': 'my value'}}.
"""
import time
from pathlib import Path
from typing import Callable

import openai
import tiktoken
from loguru import logger
from pydantic import field_validator, ValidationInfo

from . import model
from .exceptions import CompletionError
from .func import FuncCall, Function
from .msg import Message, Role, MOSHI_ROLES
from .storage import Mappable

enc: tiktoken.Encoding


def _get_function(func_name: str, available_functions: list[Callable]) -> Function:
    """Get a function from a list of available functions."""
    for func in available_functions:
        if func.__name__ == func_name:
            return Function.from_callable(func)
    raise ValueError(f"Function {func_name} not found in available functions.")


def _parse_lines(
    lines: list[str], available_functions: list[Callable] = []
) -> list[Function | Message | model.ChatM]:
    """Parse the next function or message from a list of lines."""
    if not lines:
        return []
    line = lines[0]
    parts = line.split(":")
    if parts[0].strip().lower() in model.ChatM.__members__:
        res = model.ChatM(parts[0].strip().lower())
    else:
        role = Role(parts[0].strip().lower())
        if role == Role.FUNC:
            assert len(parts) == 2
            func_name = parts[1].strip()
            res = _get_function(func_name, available_functions)
        else:
            text = ":".join(parts[1:])
            text = text.strip()
            res = Message(role, text)
    return [res] + _parse_lines(lines[1:], available_functions)


def _load_lines(fp: Path) -> list[str]:
    """load lines that aren't commented out with '#'"""
    with open(fp, "r") as f:
        _lines = f.readlines()
    lines = []
    for line in _lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        lines.append(line)
    return lines


class Prompt(Mappable):
    """ A prompt for OpenAI's API. 
    Use the self.complete() method to get the OpenAI response.
    """

    msgs: list[Message] = []
    functions: list[Function] = None
    function_call: FuncCall = None
    mod: model.ChatM = model.ChatM.GPT35TURBO

    @field_validator("msgs", mode='before')
    def coerce_string_msgs(cls, v):
        """Coerce string messages to Message objects."""
        return [Message.from_string(msg) if isinstance(msg, str) else msg for msg in v]

    @field_validator("function_call")
    def func_call_in_functions(cls, v, info: ValidationInfo):
        if v:
            if not info.data.get("functions"):
                raise ValueError("Must provide functions to use function_call.")
        return v

    @property
    def model(self) -> str:
        """e.g. 'gpt-3.5-turbo'"""
        return self.mod.value

    def to_json(self, *args, exclude_unset_functions=True, **kwargs) -> dict:
        """ Get the data to write to Firestore. """
        kwargs["exclude"] = kwargs.get("exclude", [])
        if exclude_unset_functions:
            if not self.functions:
                logger.debug("Excluding functions from json.")
                kwargs["exclude"].extend(["functions", "function_call"])
        return super().to_json(*args, **kwargs)

    @classmethod
    def from_lines(
        cls, lines: list[str], available_functions: list[Callable] = []
    ) -> "Prompt":
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
            "msgs": msgs,
            "functions": funcs,
        }
        if mod:
            kwargs["mod"] = mod.value
        return cls(**kwargs)

    @classmethod
    def from_file(cls, fp: Path, available_functions: list[Callable] = []) -> "Prompt":
        """ Parse a prompt file in this format:
        ```
        sys: Only use the functions you have been provided with.
        func: get_topic
        sys: Be polite.
        usr: Hello, how are you?
        ```
        Lines starting with '#' are ignored.
        """
        lines = _load_lines(fp)
        return cls.from_lines(lines, available_functions)

    def _biases(self, vocab: list[str], bias=5.0) -> dict[str, float]:
        """ Convert the vocab into a map from tokens to logit_biases.
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

    def _pick(self, choices: list[dict]) -> dict:
        """ Select a completion result. """
        chosen_msg = None
        for i, choice in enumerate(choices):
            index = choice.pop("index")
            finish_reason = choice.pop("finish_reason")
            msg = choice.pop("message")
            role = MOSHI_ROLES[msg["role"]]
            content = msg["content"]
            with logger.contextualize(
                index=index, finish_reason=finish_reason, role=role
            ):
                logger.debug(f"Choice {i + 1}: '{content}'")
                if role != Role.AST:
                    logger.warning(f"Expected assistant response, got {role}.")
                if not chosen_msg:
                    logger.debug("Selecting first message")
                    chosen_msg = msg
        return chosen_msg

    def complete(
        self, vocab: list[str] = [], retry_count=3, backoff_sec=5, check_user: bool = True, **kwargs
    ) -> Message | None:
        """Returns message with role and content; or None if no completion.
        Args:
            - vocab: the vocab to bias completion towards.
            - retry_count: the number of times to retry the API call.
            - backoff_sec: the number of seconds to wait between retries.
            - check_user: whether to check if the last message is from the user.
                If true (default), this function does nothing if last msg is not from usr.
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
        kwargs["n"] = kwargs.get("n", 1)
        kwargs["max_tokens"] = kwargs.get("max_tokens", 128)
        kwargs["stop"] = kwargs.get("stop", ["\n"])  # , '?', '!', '。'])
        if check_user:
            if self.msgs[-1].role == "ast":
                logger.debug("Last message is 'ast', nothing to do.")
                return None
            else:
                logger.debug(
                    "Last message is not 'ast', getting completion from model..."
                )
        logit_bias = {}
        if vocab:
            logit_bias = self._biases(vocab)
        if "logit_bias" in kwargs:
            logit_bias.update(kwargs["logit_bias"])
        logger.debug(f"Calling OpenAI API with kwargs: {kwargs}")
        logger.debug(f"retry_count={retry_count}")
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[msg.to_openai() for msg in self.msgs],
                logit_bias=logit_bias,
                **kwargs,
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
            choices = response.pop("choices")
            usage = response.pop("usage").to_dict()
            msg = None
            with logger.contextualize(**response, usage=usage, kwargs=kwargs):
                logger.debug(f"Total tokens: {usage['total_tokens']}")
                msg = self._pick(choices)
                logger.debug(f"Completion: {msg['role']:}: '{msg['content']}'")
            return Message.from_openai(msg)
        if retry_count == 0:
            logger.error("OpenAI API error: too many retries.")
            raise CompletionError("Too many retries.")
        logger.info(f"Retrying in {backoff_sec} seconds... (retry_count={retry_count})")
        time.sleep(backoff_sec)
        return self.complete(
            vocab=vocab,
            backoff_sec=backoff_sec,
            retry_count=retry_count - 1,
            check_user=check_user,
            **kwargs,
        )
