FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY services/catdog-classifier/pyproject.toml services/catdog-classifier/pyproject.toml
COPY packages/common/pyproject.toml packages/common/pyproject.toml
COPY . .
RUN uv sync --frozen --no-dev --package catdog-classifier
EXPOSE 8002
CMD ["uv", "run", "--package", "catdog-classifier", "uvicorn", "catdog_classifier.main:app", "--host", "0.0.0.0", "--port", "8002"]
