from typing import Literal

from loguru import logger
from pydantic import Field

from .storage import Versioned

class Voice(Versioned):
    """ A voice supported by Google's Text-to-Speech API. """
    bcp47: str=Field(examples=["af-ZA"])  # af-ZA  /config/voices doc -> af-ZA key -> af-ZA-Standard-A key -> data dict[str, str]
    model: str=Field(help="GCP TTS Voice model name", examples=["af-ZS-Standard-A"])  # af-ZS-Standard-A  data['model']
    language_name: str=Field(None, help="Language name", examples=["Afrikaans"])  # Afrikaans  data['language_name']
    gender: Literal[0, 1, 2] = Field(help="SSML Gender of the Google Cloud TTS Voice model, 1 is male 2 is female. Neuter not supported by Google. 0 is agnostic.", default=0)
    type: str  # Literal['WaveNet', 'Standard']  # standard  data['type']
    meta: dict[str, str]=Field(default={}, help="Metadata about the voice")

    def __init__(self, model: str, **kwargs):
        with logger.contextualize(**kwargs):
            logger.debug(f"Initializing voice: {model}")
        if not kwargs.get('bcp47'):
            kwargs['bcp47'] = '-'.join(model.split('-')[:1])
        if not kwargs.get('type'):
            kwargs['type'] = model.split('-')[-2]
        super().__init__(model=model, **kwargs)

    def __str__(self):
        res = f"{self.model} (gender={self.gender})"
        return f"V<{res}>"
