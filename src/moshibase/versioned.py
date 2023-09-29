import dataclasses
import datetime

__version__ = "23.9.2"

@dataclasses.dataclass
class Versioned:
    created_at: datetime.datetime = datetime.datetime.now()
    base_version: str = __version__