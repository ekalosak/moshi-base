import dataclasses
import datetime

__version__ = "23.9.2"

@dataclasses.dataclass
class Versioned:
    created_at: datetime.datetime = dataclasses.field(default=datetime.datetime.now())
    base_version: str = __version__

    def to_dict(self, exclude: list[str] = None) -> dict:
        """Dump the model as a dictionary."""
        if exclude is None:
            exclude = []
        return {k: v for k, v in dataclasses.asdict(self).items() if k not in exclude}