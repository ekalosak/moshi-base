"""This module provides language primitives."""
from google.cloud.firestore import DocumentSnapshot, Client, DocumentReference

import isocodes  # for country annotation
import langcodes  # for language matching
from loguru import logger
from pydantic import field_validator, Field

from .storage import FB

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
    _lang: langcodes.Language
    name: str
    country: dict[str, str]
    model: dict[str, str] = None

    def docref(self, db: Client) -> DocumentReference:
        return db.collection("languages").document(self._lang.to_tag())

    @classmethod
    def from_bcp47(cls, bcp47: str, name: str=None) -> 'Language':
        """Get the language from the line.
        Args:
            bcp47: BCP 47 language code.
            name: Language name, human readable, has format "English (United States)".
        """

        lan = langcodes.Language.get(bcp47.strip())
        cou = isocodes.countries.get(alpha_2=lan.territory)
        return cls(
            _lang=lan,
            country=cou,
            code=lan,
            name=name if name else lan.display_name(),
        )


    def __str__(self):
        try:
            res = f"{self.name} ({self.code.to_tag()} {self.model['loc']} {self.model['type']})"
        except AttributeError:
            res = f"{self.code.language_name()} ({self.code.to_tag()})"
        return f"L<{res}>"

class Voice(FB):
    """ A voice supported by Google's Text-to-Speech API. """
    name: str
    lang: Language
    model: dict[str, str]

    

    def __str__(self):
        res = f"{self.name} ({self.lang.to_tag()} {self.model['type']})"
        return f"V<{res}>"
