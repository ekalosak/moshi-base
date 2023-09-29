"""This module provides language primitives."""
import dataclasses
from difflib import SequenceMatcher

import iso639
import isocodes
from loguru import logger

def similar(a, b) -> float:
    """Return similarity of two strings.
    Source:
        - https://stackoverflow.com/a/17388505/5298555
    """
    return SequenceMatcher(None, a, b).ratio()

def match(language: str) -> str:
    """Get the closest matching language code ISO-639-1."""
    # There is spotty language coverage across libraries, so we use both
    try:
        lan = iso639.Language.match(language)
        logger.debug(f"Matched {language} to {lan} using iso639.")
        lan = lan.part1
    except iso639.language.LanguageNotFoundError:
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

@dataclasses.dataclass
class Language:
    bcp47: str

    @classmethod
    def from_str(cls, language: str):
        """Create a Language object from a string, e.g. 'en-US' or 'English'."""
        return cls(match(language))