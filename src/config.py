import yaml


class Config:
    def __init__(self, file_path: str):
        with open(file_path, "r") as f:
            self.config = yaml.safe_load(f)

    def get_model_config(self) -> dict:
        return self.config
