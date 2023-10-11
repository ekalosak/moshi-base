""" This module provides language primitives.
The Language class wraps langcodes.Language for use with Firebase.
The match function uses isocodes to match a language name to a language code.
"""
# TODO import iso639
import isocodes  # for country annotation
# from google.cloud.translate_v3 import TranslationServiceClient
from google.cloud.translate_v2 import Client as TranslationClient
import langcodes  # for language matching
from loguru import logger
from pydantic import Field

from .storage import FB, DocPath
from .voice import Voice

tra: TranslationClient = None

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

def translate(text: str, target_bcp47: str, source_bcp47: str=None) -> str:
    """ Translate text the target language. """
    global tra
    if tra is None:
        logger.debug("Initializing TranslationServiceClient...")
        tra = TranslationClient()
        logger.debug("Initialized TranslationServiceClient.")
    logger.debug(f"Translating text to {target_bcp47}: {text}")
    res = tra.translate(text, target_language=target_bcp47, source_language=source_bcp47)
    with logger.contextualize(**res):
        logger.debug(f"Translated text: {res['translatedText']}")    
    return res['translatedText']


class Language(FB):
    _language: langcodes.Language
    _country: dict[str, str]
    _bcp47: str
    meta: dict[str, str | bool] = Field(help="Metadata about the language.", default_factory=dict)
    voices: list[Voice] = Field(help="Voices supported by this language.", default_factory=list)

    def __init__(self, bcp47: str, **kwargs):
        lang: langcodes.Language = langcodes.Language.get(bcp47.strip())
        logger.debug(f"Matched bcp47={bcp47} to {lang.language_name()}")
        super().__init__(**kwargs)
        self._language = lang
        self._country: dict[str, str] = isocodes.countries.get(alpha_2=self._language.territory)
        self._bcp47 = self._language.to_tag()

    def __str__(self):
        res = f"{self.name} ({self.bcp47})"
        return f"L<{res}>"

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

    def translate(self, text: str, source_bcp47: str=None) -> str:
        return translate(text, self.bcp47, source_bcp47)
