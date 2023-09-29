"""Models of audio data."""
from .versioned import Versioned

class AudioStorage(Versioned):
    """Where the audio for a message is stored."""
    path: str
    bucket: str = None
