from abc import ABC, abstractmethod


class Model(ABC):
    @abstractmethod
    def transcribe(self, audio_file: str) -> str:
        """voice to text."""
        pass
