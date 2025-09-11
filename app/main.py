# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, users, uploads, predictions, shares, webhooks
from sqlalchemy import event
from sqlmodel import SQLModel
from app.db.engine import engine, init_models
from app.db import models

# Optional: auto-update 'updated_at' before UPDATE on Prediction
@event.listens_for(models.Prediction, "before_update", propagate=True)
def _prediction_before_update(mapper, connection, target):
    target.updated_at = target.updated_at.__class__.utcnow()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # In production use Alembic; this is handy for local dev
    # await init_models()
    pass

app = FastAPI(title="AI Website API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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