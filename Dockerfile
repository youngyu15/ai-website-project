# syntax=docker/dockerfile:1
FROM python:3.12-slim-bullseye

# OS deps (nice-to-have: curl for healthchecks; tzdata for correct logs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl tzdata ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Install uv (as you have)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# App files
WORKDIR /app
COPY . /app

# Create a non-root user (safer)
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Install deps into a venv at .venv (uv handles this)
RUN uv sync --locked --no-cache

# Expose app port
EXPOSE 8000

# Entrypoint runs DB migrations then starts the API
# (script added below)
ENTRYPOINT ["/app/.venv/bin/python", "/app/docker/entrypoint.py"]