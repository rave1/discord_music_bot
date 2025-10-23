FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    libffi-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"

WORKDIR /home/bot

COPY *.py .
COPY pyproject.toml .
COPY uv.lock .

# Sync dependencies
RUN uv sync --locked

CMD ["python", "main.py"]
