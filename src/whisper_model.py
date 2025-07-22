from model import Model
import whisper


class WhisperLocalModel(Model):
    def __init__(self, model_size: str):
        self.model = whisper.load_model(model_size)

    def transcribe(self, audio_file: str, **params) -> str:
        result = self.model.transcribe(audio_file, **params)
        return result["text"]
