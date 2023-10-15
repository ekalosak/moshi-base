""" This module provides language primitives.
The Language class wraps langcodes.Language for use with Firebase.
The match function uses isocodes to match a language name to a language code.
"""
import iso639
import isocodes  # for country annotation
from google.cloud.translate_v2 import Client as TranslationClient
import langcodes  # for language matching
from loguru import logger
from pydantic import Field, field_validator, ValidationInfo

from .exceptions import LanguageMatchError, CountryMatchError
from .storage import FB, DocPath
from .voice import Voice

tra: TranslationClient = None

def _match_isocodes(language: str) -> str:
    lan = isocodes.languages.get(name=language)['alpha_2']
    isocodes.languages.get()
    if not lan:
        lan = isocodes.languages.get(alpha_3=language)['alpha_2']
    if not lan:
        lan = isocodes.languages.get(alpha_2=language)['alpha_2']
    if not lan:
        raise ValueError(f"Could not find language for {language}")
    logger.debug(f"Matched {language} to {lan} using isocodes.")
    return lan

def _match_iso639(language: str) -> str:
    lan = iso639.to_iso639_1(language)
    if not lan:
        lan = iso639.to_iso639_2(language)
    if not lan:
        raise ValueError(f"Could not find language for {language}")
    logger.debug(f"Matched {language} to {lan} using iso639.")
    return lan

def match(language: str) -> str:
    """Get the closest matching language code ISO-639-1."""
    try:
        try:
            lan = _match_isocodes(language)
        except (KeyError, ValueError):
            lan = _match_iso639(language)
    except Exception as e:
        raise LanguageMatchError(f"Could not match language {language}") from e
    assert len(lan) in {2, 3}, f"Invalid language code: {lan}"
    return lan

def translate(text: str, target_bcp47: str, source_bcp47: str=None) -> str:
    """ Translate text the target language. """
    global tra
    if tra is None:
        logger.debug("Initializing TranslationServiceClient...")
        tra = TranslationClient()
        logger.debug("Initialized TranslationServiceClient.")
    if target_bcp47 == source_bcp47:
        logger.debug(f"Source and target languages are the same: {source_bcp47}")
        return text
    logger.debug(f"Translating text to {target_bcp47}: {text}")
    res = tra.translate(text, target_language=target_bcp47, source_language=source_bcp47)
    with logger.contextualize(**res):
        logger.debug(f"Translated text: {res['translatedText']}")    
    return res['translatedText']


class Language(FB):
    _language: langcodes.Language
    _country: dict[str, str]
    _bcp47: str
    voices: list[Voice] = Field(help="Voices supported by this language.", default=None)

    def __init__(self, bcp47: str, use_default_voice: bool=False, **kwargs):
        lang: langcodes.Language = langcodes.Language.get(bcp47.strip())
        logger.debug(f"Matched bcp47={bcp47} to {lang.language_name()}")
        super().__init__(**kwargs)
        self._language = lang
        try:
            self._country: dict[str, str] = isocodes.countries.get(alpha_2=self._language.territory)
        except Exception as e:
            raise CountryMatchError(f"Could not match country for {self._language}") from e
        self._bcp47 = self._language.to_tag()
        if not self.voices and use_default_voice:
            default_voice = Voice(model=f"{self._bcp47}-Standard-A")
            logger.debug(f"Using default voice: {default_voice}")
            self.voices = [default_voice]

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
