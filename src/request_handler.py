from src.model import Model


class RequestHandler:
    def __init__(self, model: Model):
        self.model = model

    def handle_transcription(self, audio_file: str) -> dict:
        try:
            text = self.model.transcribe(audio_file)
            return {"status": "success", "text": text}
        except Exception as e:
            return {"status": "error", "message": str(e)}
