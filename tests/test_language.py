import pytest

from moshi.exceptions import LanguageMatchError, CountryMatchError
from moshi.language import Language, match
from moshi.utils import similar

@pytest.mark.parametrize("bcp47, expected", [("Ehnglarsh", "en")])
def test_bad_match(bcp47: str, expected: str):
    with pytest.raises(LanguageMatchError):
        match(bcp47)

@pytest.mark.parametrize("bcp47, expected", [("English", "en"), ("Español", "es"), ("français", "fr"), ("Deutsch", "de"), ("русский", "ru"), ("日本語", "ja"), ("한국어", "ko"), ("中文", "zh"), ("العربية", "ar"), ("हिन्दी", "hi"), ("বাংলা", "bn"), ("Português", "pt"), ("Türkçe", "tr"), ("italiano", "it"), ("Tiếng Việt", "vi"), ("ไทย", "th"), ("עברית", "he"), ("Nederlands", "nl"), ("Ελληνικά", "el"), ("čeština", "cs"), ("Svenska", "sv"), ("Magyar", "hu")])
def test_match(bcp47: str, expected: str):
    assert match(bcp47) == expected

def test_init_fails_wo_country():
    with pytest.raises(CountryMatchError):
        Language("en")

def test_init():
    bcp47 = "en-US"
    lang = Language(bcp47)
    assert lang.bcp47 == bcp47
    assert lang.name == "English"
    assert lang.country['alpha_2'] == "US"

@pytest.mark.gcp
def test_translate():
    lang = Language("es-MX")
    text = "Hello, world!"
    translated = lang.translate(text)
    assert similar(translated, "¡Hola Mundo!") > 0.85