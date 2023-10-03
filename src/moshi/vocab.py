import dataclasses

from . import utils
from .versioned import Versioned


@dataclasses.dataclass(kw_only=True)
class Vocab(Versioned):
    term: str
    term_translation: str
    part_of_speech: str = "missing"
    definition: str = "missing"
    definition_translation: str = "missing"

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    def to_json(self) -> dict:
        return utils.jsonify(self.to_dict())