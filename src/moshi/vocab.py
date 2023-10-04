from pydantic import BaseModel


class Vocab(BaseModel):
    term: str
    term_translation: str
    part_of_speech: str = "missing"
    definition: str = "missing"
    definition_translation: str = "missing"