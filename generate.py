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

global_config = {}
with open("config.yml", "r") as f:
    global_config = yaml.safe_load(f)

os.mkdir(global_config["log_directory"])
os.mkdir(global_config["download_directory"])

docker_compose_template = Template(
    """version: '3.8'
services:
{% for config in configs %}
  {{ config.name }}:
    build:
      context: .
      dockerfile: Dockerfile
    command: ["gunicorn", "--bind", "0.0.0.0:{{ config.port }}", "--workers", "1", "app:app"]
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
  prometheus:
    image: prom/prometheus:v2.49.1
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "{{ global_config.prometheus.port }}:{{ global_config.prometheus.port }}"
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:11.1.0
    ports:
      - "{{ global_config.grafana.port }}:{{ global_config.grafana.port }}"
    environment:
      - GF_SECURITY_ADMIN_USER={{ global_config.grafana.admin_user }}
      - GF_SECURITY_ADMIN_PASSWORD={{ global_config.grafana.admin_password }}
      - GF_SERVER_ROOT_URL=http://localhost:{{ global_config.grafana.port }}
      - GF_AUTH_COOKIE_SAMESITE=lax
      - GF_AUTH_COOKIE_SECURE=false
      - GF_LOG_LEVEL={{ global_config.grafana.log_level }}
    volumes:
      - ./grafana/datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge

volumes:
  prometheus-data:
  grafana-data:"""
)

prometheus_template = Template(
    """global:
  scrape_interval: 15s
scrape_configs:
{% for config in configs %}
  - job_name: '{{ config.name }}'
    static_configs:
      - targets: ['{{ config.name }}:{{ config.prometheus_port }}']
{% endfor %}
"""
)

dockerfile_template = Template(
    """FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \\
    && ffmpeg -version \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {{ ' '.join(all_ports) }}
"""
)


datasources_template = Template(
    """apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:{{ global_config.prometheus.port }}
    isDefault: true
    access: proxy
    editable: true
"""
)

app_ports = [str(config["port"]) for config in configs]
prom_ports = [str(config["prometheus_port"]) for config in configs]
all_ports = list(set(app_ports + prom_ports))

docker_compose_content = docker_compose_template.render(
    configs=configs, global_config=global_config
)
prometheus_content = prometheus_template.render(configs=configs)
dockerfile_template_content = dockerfile_template.render(all_ports=all_ports)
datasources_template_content = datasources_template.render(global_config=global_config)

with open("Dockerfile", "w") as f:
    f.write(dockerfile_template_content)

os.makedirs("grafana", exist_ok=True)
with open("grafana/datasources.yml", "w") as f:
    f.write(datasources_template_content)

with open("docker-compose.yml", "w") as f:
    f.write(docker_compose_content)

with open("prometheus/prometheus.yml", "w") as f:
    f.write(prometheus_content)

print("Файлы успешно сгенерированы!")
