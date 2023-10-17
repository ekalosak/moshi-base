class ParseError(Exception):
    """Raised when parsing something fails."""

    ...

class CompletionError(Exception):
    """Raised when a completion fails."""

    ...

class LanguageMatchError(Exception):
    """Raised when a language match fails."""

    ...

class CountryMatchError(Exception):
    """Raised when a country match fails."""

    ...


class TemplateNotSubstitutedError(Exception):
    """Raised when a template is not substituted."""

    ...

class ScoreParseError(ParseError):
    """ Raised when a score cannot be parsed. """

    ...
