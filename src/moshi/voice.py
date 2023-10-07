from typing import Literal

from .storage import Versioned

class Voice(Versioned):
    """ A voice supported by Google's Text-to-Speech API. """
    bcp47: str
    name: str
    language_name: str = None
    ssml_gender: int
    type: Literal['Wavenet', 'Standard']

    def __init__(self, name: str, gender: int, **kwargs):
        if not kwargs.get('bcp47'):
            kwargs['bcp47'] = '-'.join(name.split('-')[:1])
        if not kwargs.get('type'):
            kwargs['type'] = name.split('-')[-2]
        super().__init__(name=name, ssml_gender=gender, **kwargs)

    def __str__(self):
        res = f"{self.name} (gender={self.ssml_gender})"
        return f"V<{res}>"

    def create(self, client):
        """ Create the voice in the database. """
        