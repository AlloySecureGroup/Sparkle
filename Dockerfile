FROM python:3.11-slim

WORKDIR /sparkle

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sparkle_engine.py .
COPY sparkle_api.py .
COPY sparkle_openai_compat.py .
COPY sparkle_analyzer.py .
COPY sparkle_config.json .
COPY secrets.yaml .

RUN mkdir -p sparkle_logs

EXPOSE 5000

ENV SPARKLE_PORT=5000
ENV SPARKLE_DEBUG=false
ENV PYTHONUNBUFFERED=1
# Runtime override: point at a different secrets file without rebuilding,
# e.g. `docker run -e SPARKLE_SECRETS_FILE=/sparkle/custom_secrets.yaml ...`
ENV SPARKLE_SECRETS_FILE=secrets.yaml
# Runtime rename: change the display name without rebuilding,
# e.g. `docker run -e SPARKLE_NAME=MyAssistant ...`
ENV SPARKLE_NAME=Sparkle

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "sparkle_openai_compat.py"]
