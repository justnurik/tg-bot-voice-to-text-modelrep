from model import Model
import requests


class OpenAIApiModel(Model):
    def __init__(self, api_key: str, endpoint: str):
        self.api_key = api_key
        self.endpoint = endpoint

    def transcribe(self, audio_file: str, **params) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        with open(audio_file, "rb") as f:
            response = requests.post(
                self.endpoint, headers=headers, files={"file": f}, **params
            )
            response.raise_for_status()
            return response.json()["text"]
