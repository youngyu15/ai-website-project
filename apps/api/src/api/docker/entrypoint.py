# /app/docker/entrypoint.py
import os, subprocess, sys, time

def run(cmd: list[str]) -> int:
    print("+", " ".join(cmd), flush=True)
    return subprocess.call(cmd)

# Optional: wait a bit if DB might not be ready yet (Compose healthcheck is better)
time.sleep(int(os.getenv("STARTUP_DELAY", "0")))

# 1) Run Alembic migrations (ignore if alembic not configured)
if os.environ.get("RUN_MIGRATIONS", "1") == "1":
    rc = run(["/app/.venv/bin/alembic", "upgrade", "head"])
    if rc != 0:
        sys.exit(rc)

# 2) Start the API (uvicorn recommended)
host = os.getenv("HOST", "0.0.0.0")
port = os.getenv("PORT", "8000")
rc = run([
    "/app/.venv/bin/uvicorn",
    "app.main:app",
    "--host", host,
    "--port", port,
    "--proxy-headers",
    "--forwarded-allow-ips", "*"
])
sys.exit(rc)
