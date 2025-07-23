import os
import yaml
from jinja2 import Template

config_dir = "configs"
config_files = [f for f in os.listdir(config_dir) if f.endswith(".yml")]

configs = []
for file in config_files:
    with open(os.path.join(config_dir, file), "r") as f:
        config_data = yaml.safe_load(f)
        config_data["filename"] = file
        configs.append(config_data)

with open("config.yml", "r") as f:
    global_config = yaml.safe_load(f)

os.makedirs(global_config["log_directory"], exist_ok=True)
os.makedirs(global_config["download_directory"], exist_ok=True)

docker_compose_template = Template(
    """version: '3.8'
services:
{% for config in configs %}
  {{ config.name }}:
    build:
      context: .
      dockerfile: Dockerfile
    command: ["gunicorn", "--bind", "0.0.0.0:{{ config.port }}", "--workers", "1", "--timeout", "600", "app:app"]
    environment:
      - CONFIG_PATH=configs/{{ config.filename }}
    ports:
      - "{{ config.port }}:{{ config.port }}"
      - "{{ config.prometheus_port }}:{{ config.prometheus_port }}"
    volumes:
      - ./logs:/app/{{ global_config.log_directory }}
      - ./downloads:/app/{{ global_config.download_directory }}
    networks:
      - monitoring
{% endfor %}

networks:
  monitoring:
    driver: bridge
"""
)

dockerfile_template = Template(
    """FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && ffmpeg -version \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {{ ' '.join(all_ports) }}
"""
)

app_ports = [str(config["port"]) for config in configs]
prom_ports = [str(config["prometheus_port"]) for config in configs]
all_ports = list(set(app_ports + prom_ports))

with open("Dockerfile", "w") as f:
    f.write(dockerfile_template.render(all_ports=all_ports))

with open("docker-compose.yml", "w") as f:
    f.write(
        docker_compose_template.render(configs=configs, global_config=global_config)
    )

print("Файлы успешно сгенерированы!")
