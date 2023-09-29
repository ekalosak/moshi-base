"""Datamodels of GPT model configurations.
Source:
    - https://platform.openai.com/docs/api-reference/models
"""
from enum import Enum

class CompletionM(str, Enum):
    """Completion models don't use roles."""
    TEXTDAVINCI003 = "text-davinci-003"
    TEXTDAVINCI002 = "text-davinci-002"
    TEXTCURIE001 = "text-curie-001"
    TEXTBABBAGE001 = "text-babbage-001"
    TEXTADA001 = "text-ada-001"

class ChatM(str, Enum):
    """Chat completion models do use roles."""
    GPT35TURBO = "gpt-3.5-turbo"
    GPT35TURBO0301 = "gpt-3.5-turbo-0301"