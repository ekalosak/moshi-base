from typing import Literal

from moshi.storage import FB

class Voice(FB):
    """ A voice supported by Google's Text-to-Speech API. """
    bcp47: str
    name: str
    language_name: str
    ssml_gender: int
    type: Literal['Wavenet', 'Standard']

    def __str__(self):
        res = f"{self.name} (gender={self.ssml_gender})"
        return f"V<{res}>"