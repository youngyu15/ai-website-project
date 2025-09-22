from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth, users, uploads, predictions, shares, webhooks

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/v1/users", tags=["users"])
app.include_router(uploads.router, prefix="/v1/uploads", tags=["uploads"])
app.include_router(predictions.router, prefix="/v1/predictions", tags=["predictions"])
app.include_router(shares.router, prefix="/v1/shares", tags=["shares"])
app.include_router(webhooks.router, prefix="/v1/webhooks", tags=["webhooks"])