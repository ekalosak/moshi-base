"""Common utilities for base types, functions, classes, etc."""
from datetime import datetime, timezone
from difflib import SequenceMatcher
import uuid

def _toRFC3339(dt: datetime):
    """Convert a datetime to RFC3339."""
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

def utcnow() -> datetime:
    """ Get the current UTC datetime, avoiding the bullshit of datetime.utcnow().
    See https://blog.ganssle.io/articles/2019/11/utcnow.html for more details.
    """
    return datetime.now(timezone.utc)

def random_string(length: int=6) -> str:
    """ Generate a random string of ASCII letters. """
    import random
    import string
    return ''.join(random.choice(string.ascii_letters + string.digits) for i in range(length))

def id_prefix(uidlen = 12) -> str:
    """ Generate a unique ID prefix. """
    prefix = random_string(uidlen)
    date = datetime.now().strftime("%y%m%d-%H%M%S")
    return f"{prefix}-{date}"

def jsonify(obj):
    """Convert an object to JSON serializable."""
    if hasattr(obj, "isoformat"):
        return _toRFC3339(obj)
    if hasattr(obj, "to_json"):
        return obj.to_json()
    return str(obj)

def confirm(msg: str, require_confirmation: bool=True) -> None:
    """ Confirm an action with the user. Used in interactive sessions on the CLI. """
    from loguru import logger
    if not require_confirmation:
        logger.warning(f"Skipping confirmation for {msg}.")
        return
    ok = input(f"{msg}? (y/n) ")
    if ok != 'y':
        logger.warning(f"Aborting {msg}.")
        exit(1)
    else:
        logger.debug(f"Confirmed {msg}.")

def similar(a: str, b: str) -> float:
    """Return similarity of two strings.
    Source:
        - https://stackoverflow.com/a/17388505/5298555
    """
    return SequenceMatcher(None, a, b).ratio()

def flatten(dat: dict) -> dict:
    """ Flatten a nested dict.
    Examples:
        {'foo': {'bar': 1}} -> {'foo.bar': 1}
    """
    res = {}
    for k, v in dat.items():
        if isinstance(v, dict):
            for k2, v2 in flatten(v).items():
                res[f"{k}.{k2}"] = v2
        else:
            res[k] = v
    return res