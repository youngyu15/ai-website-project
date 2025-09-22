FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY packages/common/pyproject.toml packages/common/pyproject.toml
COPY . .
RUN uv sync --frozen --no-dev --package api
EXPOSE 8000
CMD ["uv","run","--package","api","uvicorn","api.main:app","--host","0.0.0.0","--port","8000"]
