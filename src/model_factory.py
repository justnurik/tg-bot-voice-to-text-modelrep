from whisper_model import WhisperLocalModel
from openai_api_model import OpenAIApiModel


class ModelFactory:
    @staticmethod
    def create_model(config: dict):
        model_type = config.get("type")
        if model_type == "local":
            return WhisperLocalModel(config["model_size"])
        elif model_type == "api":
            return OpenAIApiModel(config["api_key"], config["url"])
        else:
            raise ValueError(f"Unknown model type: {model_type}")
