"""Models of audio data."""
from .storage import FB

class AudioStorage(FB):
    """Where the audio for a message is stored."""
    path: str
    bucket: str = None
