"""Datamodels of GPT model configurations."""
from enum import Enum

class ModelType(str, Enum):
    """The two model types used by this app.
    Source:
        - https://platform.openai.com/docs/api-reference/models
    """
    COMP = "completion"
    CHAT = "chat_completion"

class Model(Enum, str):
    _type: ModelType

class CompletionM(Model):
    """Completion models don't use roles."""
    _type = ModelType.COMP
    TEXTDAVINCI003 = "text-davinci-003"
    TEXTDAVINCI002 = "text-davinci-002"
    TEXTCURIE001 = "text-curie-001"
    TEXTBABBAGE001 = "text-babbage-001"
    TEXTADA001 = "text-ada-001"

class ChatM(Model):
    """Chat completion models do use roles."""
    _type = ModelType.CHAT
    GPT35TURBO = "gpt-3.5-turbo"
    GPT35TURBO0301 = "gpt-3.5-turbo-0301"