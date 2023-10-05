from enum import Enum
import os
import random
from typing import Callable

from google.auth.exceptions import DefaultCredentialsError
from google.cloud import firestore
from loguru import logger
import pytest

from moshi.activ import MinA

GCLOUD_PROJECT = os.getenv("GCLOUD_PROJECT", "demo-test")
logger.info(f"GCLOUD_PROJECT={GCLOUD_PROJECT}")

@pytest.fixture
def uid() -> str:
    return 'test-user'

@pytest.fixture
def bcp47() -> str:
    return 'en-US'

@pytest.fixture
def mina():
    return MinA('en-US')

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

@pytest.fixture(scope="module")
def db():
    """Create a firestore client."""
    try:
        db = firestore.Client(GCLOUD_PROJECT)
    except DefaultCredentialsError:
        logger.warning("Could not find default credentials")
        db = firestore.Client()
    print(f"Created db client, project={db.project}, database={db._database}, target={db._target}")
    return db