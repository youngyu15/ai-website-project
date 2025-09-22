FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY services/face-detection/pyproject.toml services/face-detection/pyproject.toml
COPY packages/common/pyproject.toml packages/common/pyproject.toml
COPY . .
RUN uv sync --frozen --no-dev --package face-detection
EXPOSE 8001
CMD ["uv", "run", "--package", "face-detection", "uvicorn", "face_detection.main:app", "--host", "0.0.0.0", "--port", "8001"]
