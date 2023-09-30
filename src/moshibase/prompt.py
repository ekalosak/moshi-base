import dataclasses
from pathlib import Path

from loguru import logger

from moshibase import Versioned, Message, Role

@dataclasses.dataclass(kw_only=True)
class Prompt(Versioned):
    """A prompt for OpenAI's API."""
    fn: Path
    _msgs: list[Message] = dataclasses.field(default_factory=list)

    @property
    def msgs(self):
        return self._msgs

    def parse_prompt_file(self, strict=True) -> list[Message]:
        """Parse a prompt file in 'usr: ...\\nast: ...' format.
        Lines starting with '#' are ignored."""
        with open(self.fn, 'r') as f:
            _lines = f.readlines()
        lines = []
        for line in _lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                continue
            lines.append(line)
        msgs = []
        for line in lines:
            parts = line.split(':')
            try:
                role = Role(parts[0].strip().lower())
            except ValueError:
                if not strict:
                    logger.warning(f"Invalid role {role}")
                    continue
                else:
                    raise ValueError(f"Invalid role {role}; try setting strict=False")
            text = ':'.join(parts[1:])
            text = text.strip()
            msg = Message(role, text)
            msgs.append(msg)
        if not msgs:
            logger.warning(f"No messages found in {self.fn}")
        if not self._msgs:
            self._msgs = msgs
        return msgs