"""This module provides language primitives."""
from pathlib import Path

from google.cloud.firestore import DocumentSnapshot, Client, DocumentReference

import isocodes  # for country annotation
import langcodes  # for language matching
from loguru import logger
from pydantic import field_validator, Field, ValidationInfo

from .storage import FB, DocPath

def match(language: str) -> str:
    """Get the closest matching language code ISO-639-1."""
    lan = isocodes.languages.get(name=language)['alpha_2']
    if not lan:
        lan = isocodes.languages.get(alpha_3=language)['alpha_2']
    if not lan:
        lan = isocodes.languages.get(alpha_2=language)['alpha_2']
    if not lan:
        raise ValueError(f"Could not find language for {language}")
    logger.debug(f"Matched {language} to {lan} using isocodes.")
    assert len(lan) in {2, 3}, f"Invalid language code: {lan}"
    return lan

class Language(FB):
    _language: langcodes.Language
    _country: dict[str, str]

    def __init__(self, bcp47: str, **kwargs):
        super().__init__(**kwargs)
        self._language: langcodes.Language = langcodes.Language.get(bcp47.strip())
        self._country: dict[str, str] = isocodes.countries.get(alpha_2=self._language.territory)

    @property
    def docpath(self) -> DocPath:
        return DocPath(f'languages/{self.bcp47}')

    @property
    def bcp47(self) -> str:
        return self._language.to_tag()
    
    @property
    def name(self) -> str:
        return self._language.language_name()

    def __str__(self):
        res = f"{self.name} ({self.bcp47})"
        return f"L<{res}>"

class Voice(FB):
    """ A voice supported by Google's Text-to-Speech API. """
    name: str
    lang: Language
    model: dict[str, str]

    def __str__(self):
        res = f"{self.name} ({self.lang.bcp47})"
        return f"V<{res}>"
