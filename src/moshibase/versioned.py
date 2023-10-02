import dataclasses
import datetime
import json

from .utils import jsonify

__version__ = "23.9.3"

@dataclasses.dataclass(kw_only=True)
class Versioned:
    created_at: datetime.datetime = dataclasses.field(default=datetime.datetime.now())
    base_version: str = __version__

    def to_dict(self, exclude: list[str] = None) -> dict:
        """Dump the model as a dictionary."""
        if exclude is None:
            exclude = []
        return {k: v for k, v in dataclasses.asdict(self).items() if k not in exclude}

    def to_jsons(self, exclude: list[str] = None) -> str:
        """Dump the model as a JSON string."""
        return json.dumps(self.to_dict(exclude=exclude), default=lambda o: jsonify(o))

    def to_json(self, exclude: list[str] = None) -> dict:
        """Dump the model as a JSON object."""
        return json.loads(self.to_jsons(exclude=exclude))
