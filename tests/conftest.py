from enum import Enum
import random
from typing import Callable

import pytest

@pytest.fixture
def get_topic() -> Callable:
    def get_topic():
        """ Come up with a topic to talk about. """
        import random
        return random.choice(["sports", "politics", "the weather", "media", "science"])
    return get_topic

class SSMLGender(str, Enum):
    MALE = '1'
    FEMALE = '2'
    OTHER = '3'

@pytest.fixture
def get_name() -> Callable:
    def get_name(bcp47: str, ssml_gender: SSMLGender=SSMLGender.MALE, number: int=1) -> list[str]:
        """ Get a random name. 
        Args:
            bcp47: The BCP-47 language code to use to pick the name.
            ssml_gender: The SSML gender to use to pick the name.
            number: The number of names to return.
        """
        return random.choices(["John", "Jane", "Bob", "Alice"], k=number)
    return get_name
