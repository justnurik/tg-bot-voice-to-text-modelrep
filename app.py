import os
from time import time
from prometheus_client import Counter, Histogram, start_http_server
from flask import Flask, request
from src.config import Config
from src.model_factory import ModelFactory
from src.logger import setup_logger

global_config_path = "config.yml"
global_config = Config(global_config_path).to_dict()
config_path = os.getenv("CONFIG_PATH")
config = Config(config_path)
model_config = config.to_dict()
model = ModelFactory.create_model(model_config)

print("[MODEL CONFIG]", model_config)

log_file = f"{global_config['log_directory']}/{model_config.get('log_file', f'model_{model_config['name']}.log')}"
logger = setup_logger(
    model_config["name"], log_file, model_config.get("log_level", "INFO")
)
logger.info(
    f"Starting server for model {model_config["name"]} on port {model_config['port']}"
)

app = Flask(__name__)

REQUEST_COUNT = Counter("request_count", "Total number of requests")
TRANSCRIBE_TIME = Histogram(
    "transcribe_duration_seconds", "Time spent in transcribe function"
)
RESULT_LENGTH = Histogram("result_length_chars", "Length of transcription result")
AUDIO_LENGTH = Histogram("audio_length_seconds", "Length of audio file in seconds")


@app.route("/transcriptions", methods=["POST"])
def transcribe():
    logger.info(f"Received transcription request from {request.remote_addr}")

    REQUEST_COUNT.inc()

    if "audio" not in request.files:
        logger.error(
            f"Transcription failed for {request.remote_addr}, error: No audio file provided"
        )
        return {"error": "No audio file provided"}, 400

    audio_data = request.files["audio"].read()
    audio_length = len(audio_data) / 16000
    AUDIO_LENGTH.observe(audio_length)

    import tempfile

    with tempfile.NamedTemporaryFile(
        dir=global_config["download_directory"], delete=True
    ) as temp_audio_file:
        temp_audio_file.write(audio_data)
        temp_audio_file.flush()

        start_time = time()
        result = model.transcribe(temp_audio_file.name, fp16=False)
        TRANSCRIBE_TIME.observe(time() - start_time)
        RESULT_LENGTH.observe(len(result))

        logger.info(
            f"Transcription completed for {request.remote_addr}, result: {result}"
        )

        return {"transcription": result}, 200

if model_config.get("prometheus_port"):
    logger.info(f"Starting Prometheus metrics server on port {model_config['prometheus_port']}")
    start_http_server(model_config['prometheus_port'])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=model_config["port"])
