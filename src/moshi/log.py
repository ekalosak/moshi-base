"""Call setup_loguru() to configure loguru logging for your environment.
These environment variables configure the logger:
    - ENV: "dev" or "prod", defaults to "prod"
    - LOG_LEVEL: "TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL", defaults to "DEBUG"
    - LOG_FORMAT: "json" or "rich", defaults to "json"
"""
import functools
import json
import os
import time
from typing import Callable, TypeVar, ParamSpec

import loguru
from loguru import logger
from loguru._defaults import LOGURU_FORMAT

from .utils import jsonify

LOGURU_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level.icon} {level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> | <g><d>{extra}</d></g>"

ENV = os.getenv("ENV", "prod")
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # either json or anything else
LOG_COLORIZE = int(os.getenv("LOG_COLORIZE", 0))
LOG_COLORIZE = (ENV == "dev" or LOG_COLORIZE or LOG_FORMAT == "rich")
logger.info(f"ENV={ENV} LOG_LEVEL={LOG_LEVEL} LOG_FORMAT={LOG_FORMAT} LOG_COLORIZE={LOG_COLORIZE}")
if ENV == "dev":
    logger.warning("Running in dev mode. Logs will be verbose and include sensitive diagnostic data.")

def failed(exc: Exception, msg: str = None, level: str = "CRITICAL"):
    """Log an error raised to the top of the stack that caused e.g. a firebase function to fail."""
    payload = f"{msg}: {exc}"
    logger.opt(depth=1, exception=exc).log(level, payload)

P = ParamSpec("P")  # required to retain type hints for decorated functions
T = TypeVar("T")

def traced(f: Callable[P, T], msg: str = None, verbose = False, depth=1) -> Callable[P, T]:
    msg = msg or f.__name__
    @functools.wraps(f)
    def wrapper(*a: P.args, **k: P.kwargs):
        with logger.contextualize(**k if verbose else {}):
            t0 = time.monotonic()
            logger.opt(depth=depth).trace(f"[START] {msg}")
            result = f(*a, **k)
            logger.opt(depth=depth).trace(f"[END] {msg} ({time.monotonic() - t0:.3f}s)")
        return result
    return wrapper

def _gcp_log_severity_map(level: str) -> str:
    """Convert loguru custom levels to GCP allowed severity level.
    Source:
        - https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#LogSeverity
    """
    match level:
        case "SUCCESS":
            return "INFO"
        case "TRACE":
            return "DEFAULT"
        case _:
            return level

def _format_timedelta(td) -> str:
    return f"{td.days}days{td.seconds}secs{td.microseconds}usecs"

def _toGCPFormat(rec: loguru._handler.Message) -> str:
    """Convert a loguru record to a gcloud structured logging payload."""
    rec = rec.record
    rec["severity"] = _gcp_log_severity_map(rec["level"].name)
    rec.pop("level")
    if not rec["extra"]:
        rec.pop("extra")
    rec["elapsed"] = _format_timedelta(rec["elapsed"])
    if "exception" in rec:
        if rec["exception"] is not None:
            rec["exception"] = str(rec["exception"])
        else:
            rec.pop("exception")
    rec["file"] = rec["file"].name  # also .path
    rec["process_id"] = rec["process"].id
    rec["process_name"] = rec["process"].name
    rec.pop("process")
    rec["thread_id"] = rec["thread"].id
    rec["thread_name"] = rec["thread"].name
    rec.pop("thread")
    return json.dumps(rec, default=lambda o: jsonify(o))

def setup_loguru(fmt=LOG_FORMAT, sink=print, level=LOG_LEVEL, diagnose=False):
    print("Adding stdout logger...")
    colorize = LOG_COLORIZE
    diagnose = diagnose or ENV == "dev"
    if fmt == "json":
        print("Using JSON formatter...")
        def _sink(rec):
            sink(_toGCPFormat(rec) + "\n")
    else:
        print("Using LOGURU formatter...")
        _sink = sink
    for lvl, no, color, icon in [
        ("DETAIL", 1, "<blue>", "🔬",),
        ("TRACE", 5, "<blue>", "⏱",),
        ("DEBUG", 10, "<cyan>", "🐛",),
        ("TRANSCRIPT", 15, "<magenta>", "📜",),
        ("INFO", 20, "<white>", "💡",),
        ("SUCCESS", 25, "<green>", "✅",),
        ("WARNING", 30, "<yellow>", "🚧",),
        ("ERROR", 40, "<red>", "❌",),
        ("CRITICAL", 50, "<RED>", "🚨",),
        ("ALERT", 60, "<RED><bold>", "🚨🚨",),
        ("EMERGENCY", 70, "<RED><bold>", "🚨🚨🚨",),
    ]:
        try:
            logger.level(lvl, no=no, color=color, icon=icon)
        except TypeError as e:
            logger.level(lvl, color=color, icon=icon)
    logger.remove()
    logger.add(_sink,
        diagnose=diagnose,
        level=level,
        format=LOGURU_FORMAT,
        colorize=colorize,
    )
    print("Logger setup complete.")

# TODO should be in moshifx
def log_event(fn):
    """ Decorator to log the event params in firebase functions. """
    @functools.wraps(fn)
    def wrapper(event: 'Event[DocumentSnapshot]'):  # firebase_functions.firestore_fn.Event, DocumentSnapshot
        with logger.contextualize(**event.params):
            return fn(event)
    return wrapper
