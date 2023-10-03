"""Common utilities for base types, functions, classes, etc."""
from datetime import datetime, timezone

def _toRFC3339(dt: datetime):
    """Convert a datetime to RFC3339."""
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

def jsonify(obj):
    """Convert an object to JSON serializable."""
    if hasattr(obj, "isoformat"):
        return _toRFC3339(obj)
    if hasattr(obj, "to_json"):
        return obj.to_json()
    return str(obj)

def random_string(length: int=6) -> str:
    """ Generate a random string of ASCII letters. """
    import random
    import string
    return ''.join(random.choice(string.ascii_letters) for i in range(length))

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