""" This module provides the `select_vocabulary` function.
Use it to select the vocabulary to use for new activity plans.
"""
from datetime import UTC, datetime

from moshi.vocab.usage import UsageV


def select_vocabulary(vocs: dict[str, UsageV], n=16, max_usg=4, recent: datetime=None) -> list[str]:
    """ Select the vocabulary to use for new activity plans.
    This early implementation returns terms that the user has used less than a certain number of times, prioritizing those used most recently.
    Later versions will be enriched with more sophisticated selection methods:
    - based on curriculum
    - based on user interests
    - based on user goals
    - based on correctness of usage
    - conditional on the activity type, topic, level, etc.
    Args:
        vocs: user's vocabulary usage, from User.get_vocab(db).
        n: max number of terms to select.
    """
    if not recent:
        recent = datetime.now(UTC)
    terms = []
    for term, usg in vocs.items():
        if usg.count < max_usg:
            terms.append(term)
    if len(terms) < n:
        return terms
    else:
        return sorted(terms, key=lambda t: (vocs[t].last - recent).total_seconds())[:n]