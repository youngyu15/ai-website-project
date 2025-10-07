from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import api.settings
from api.settings import settings
from api.db.models import User
from api.deps import get_current_user
from uuid import UUID, uuid4
from api.routers import auth_router, users_router, uploads_router, predictions_router, shares_router, webhooks_router

app = FastAPI(title=settings.app_name, version="1.0.0")

@app.get("/health")
def health():
    return {"status": True}

def _dev_user() -> User:
    # return a lightweight user object consistent with your code
    return User(id=(UUID(settings.DEV_USER_ID) if settings.DEV_USER_ID else uuid4()),
                email="dev@example.com", password_hash="")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-CSRF-Token",
    ],
)

app.include_router(auth_router.router, prefix="/v1/auth", tags=["auth"])
app.include_router(users_router.router, prefix="/v1/users", tags=["users"])
app.include_router(uploads_router.router, prefix="/v1/uploads", tags=["uploads"])
app.include_router(predictions_router.router, prefix="/v1/predictions", tags=["predictions"])
app.include_router(shares_router.router, prefix="/v1/shares", tags=["shares"])
app.include_router(webhooks_router.router, prefix="/v1/webhooks", tags=["webhooks"])

app.mount("/static/uploads", StaticFiles(directory="./var/uploads"), name="uploads")