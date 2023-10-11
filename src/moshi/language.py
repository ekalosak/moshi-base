"""This module provides language primitives."""
from pathlib import Path

from google.cloud.firestore import DocumentSnapshot, Client, DocumentReference

# TODO import iso639
import isocodes  # for country annotation
import langcodes  # for language matching
from loguru import logger
from pydantic import Field

from .storage import FB, DocPath
from .voice import Voice

def match(language: str) -> str:
    """Get the closest matching language code ISO-639-1."""
    lan = isocodes.languages.get(name=language)['alpha_2']
    if not lan:
        lan = isocodes.languages.get(alpha_3=language)['alpha_2']
    if not lan:
        lan = isocodes.languages.get(alpha_2=language)['alpha_2']
    if not lan:
        raise ValueError(f"Could not find language for {language}")
    # logger.debug(f"Matched {language} to {lan} using isocodes.")
    assert len(lan) in {2, 3}, f"Invalid language code: {lan}"
    return lan

class Language(FB):
    _language: langcodes.Language
    _country: dict[str, str]
    _bcp47: str
    meta: dict[str, str | bool] = Field(help="Metadata about the language.", default_factory=dict)
    voices: list[Voice] = Field(help="Voices supported by this language.", default_factory=list)

    def __init__(self, bcp47: str, **kwargs):
        lang: langcodes.Language = langcodes.Language.get(bcp47.strip())
        # logger.debug(f"Matched bcp47={bcp47} to {lang.language_name()}")
        super().__init__(**kwargs)
        self._language = lang
        self._country: dict[str, str] = isocodes.countries.get(alpha_2=self._language.territory)
        self._bcp47 = self._language.to_tag()

    @property
    def docpath(self) -> DocPath:
        return DocPath(f'languages/{self.bcp47}')

    @property
    def bcp47(self) -> str:
        return self._bcp47
    
    @property
    def name(self) -> str:
        return self._language.language_name()

    @property
    def code(self) -> langcodes.Language:
        return self._language
    
    @property
    def country(self) -> dict[str, str]:
        return self._country

    def __str__(self):
        res = f"{self.name} ({self.bcp47})"
        return f"L<{res}>"